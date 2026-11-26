"""Protección de /auth y flujo del webhook de WhatsApp."""
import asyncio
import json
import time
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth import auth_controller
from auth.auth_controller import create_auth_router
from auth.google_auth_manager import AccountNotAllowedError, GoogleAuthManager
from whatsapp.whatsapp_service import WhatsAppService

CLIENT_SECRET = {
    "web": {
        "client_id": "test.apps.googleusercontent.com",
        "client_secret": "secret",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8000/auth/callback"],
    }
}


@pytest.fixture
def manager(tmp_path):
    secret = tmp_path / "client_secret.json"
    secret.write_text(json.dumps(CLIENT_SECRET))
    return GoogleAuthManager(
        client_secret_path=secret,
        token_path=tmp_path / "token.json",
        redirect_uri="http://localhost:8000/auth/callback",
        allowed_emails=("dueno@example.com",),
    )


def client_for(manager, password="clave-larga"):
    app = FastAPI()
    app.include_router(create_auth_router(manager, admin_user="admin", admin_password=password))
    return TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def no_delay(monkeypatch):
    monkeypatch.setattr(auth_controller, "FAILED_LOGIN_DELAY_SECONDS", 0)


@pytest.mark.parametrize("path, method", [("/auth/login", "get"), ("/auth/status", "get"),
                                          ("/auth/refresh-token", "post")])
def test_auth_endpoints_require_basic_credentials(manager, path, method):
    client = client_for(manager)
    response = getattr(client, method)(path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")
    response = getattr(client, method)(path, auth=("admin", "incorrecta"))
    assert response.status_code == 401


def test_login_redirects_to_google_with_valid_credentials(manager):
    response = client_for(manager).get("/auth/login", auth=("admin", "clave-larga"))
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://accounts.google.com/")


def test_login_disabled_without_configured_password(manager):
    response = client_for(manager, password="").get("/auth/login", auth=("admin", ""))
    assert response.status_code == 503


def test_callback_rejects_unknown_state(manager):
    response = client_for(manager).get("/auth/callback?code=abc&state=inventado")
    assert response.status_code == 400
    assert not manager._token_path.exists()


def test_callback_rejects_account_not_in_allowed_list(manager, monkeypatch):
    client = client_for(manager)
    location = client.get("/auth/login", auth=("admin", "clave-larga")).headers["location"]
    state = dict(p.split("=", 1) for p in location.split("?", 1)[1].split("&"))["state"]

    fake_flow = SimpleNamespace(fetch_token=lambda **_: None, credentials=SimpleNamespace(to_json=lambda: "{}"))
    monkeypatch.setattr(manager, "_build_flow", lambda: fake_flow)
    monkeypatch.setattr(manager, "fetch_account_email", lambda _c: "intruso@example.com")

    response = client.get(f"/auth/callback?code=abc&state={state}")
    assert response.status_code == 403
    assert not manager._token_path.exists()


def test_allowed_account_saves_token(manager, monkeypatch):
    manager._pending_states["s1"] = (None, __import__("time").monotonic())
    fake_flow = SimpleNamespace(fetch_token=lambda **_: None,
                                credentials=SimpleNamespace(to_json=lambda: '{"ok": 1}'))
    monkeypatch.setattr(manager, "_build_flow", lambda: fake_flow)
    monkeypatch.setattr(manager, "fetch_account_email", lambda _c: "Dueno@Example.com")
    manager.complete_authorization(code="abc", state="s1", authorization_response="http://x")
    assert manager._token_path.read_text() == '{"ok": 1}'

    manager._pending_states["s2"] = (None, __import__("time").monotonic())
    monkeypatch.setattr(manager, "fetch_account_email", lambda _c: "otro@example.com")
    with pytest.raises(AccountNotAllowedError):
        manager.complete_authorization(code="abc", state="s2", authorization_response="http://x")


def test_expired_state_is_rejected(manager):
    manager._pending_states["viejo"] = (None, -10_000.0)
    with pytest.raises(ValueError):
        manager.complete_authorization(code="abc", state="viejo", authorization_response="http://x")


# ----------------------------------------------------------------------
# WhatsApp: respuesta inmediata y procesamiento en segundo plano
# ----------------------------------------------------------------------
class FakeAccounting:
    def __init__(self, delay: float = 0.0):
        self.calls = []
        self.delay = delay

    def handle_commands(self, phone, commands):
        time.sleep(self.delay)          # corre en un hilo (asyncio.to_thread)
        self.calls.append((phone, commands))
        return [f"ok {c}" for c in commands] or ["sin comandos"]

    def has_pending_selection(self, phone):
        return False


class FakeDeepSeek:
    def __init__(self, delays: dict[str, float] | None = None):
        self.delays = delays or {}

    async def extract_commands(self, text):
        await asyncio.sleep(self.delays.get(text, 0))
        if text == "jajaja ok":
            return []
        return [part.strip() for part in text.split(" y ")]


def webhook(text, message_id="ID1", phone="999"):
    return {"data": {"key": {"remoteJid": f"{phone}@s.whatsapp.net", "id": message_id},
                     "messageType": "conversation", "message": {"conversation": text}}}


def make_service(accounting=None, deepseek=None):
    accounting = accounting or FakeAccounting()
    service = WhatsAppService("http://evo", "inst", "tok", None, deepseek or FakeDeepSeek(), accounting)
    sent = []

    async def fake_send(to, message):
        sent.append(message)

    service.send_message = fake_send
    return service, accounting, sent


def test_webhook_answers_immediately_and_processes_in_background():
    service, accounting, sent = make_service(FakeAccounting(delay=0.3))

    async def scenario():
        started = time.monotonic()
        assert service.accept(webhook("gasto 5000 pan y gasto 3000 leche")) == "received"
        assert time.monotonic() - started < 0.05          # no esperó el procesamiento
        assert service.status("ID1") == "processing" and sent == []
        await service.wait_idle()

    asyncio.run(scenario())
    assert service.status("ID1") == "done"
    assert accounting.calls == [("999", ["gasto 5000 pan", "gasto 3000 leche"])]
    assert sent == ["ok gasto 5000 pan", "ok gasto 3000 leche"]


def test_duplicate_message_id_is_processed_once():
    service, accounting, sent = make_service()

    async def scenario():
        assert service.accept(webhook("gasto 5000 pan", "DUP")) == "received"
        assert service.accept(webhook("gasto 5000 pan", "DUP")) == "duplicate"
        await service.wait_idle()
        assert service.accept(webhook("gasto 5000 pan", "DUP")) == "duplicate"   # también después

    asyncio.run(scenario())
    assert accounting.calls == [("999", ["gasto 5000 pan"])]


def test_messages_from_the_same_sender_keep_their_order():
    # El primero tarda más en DeepSeek: sin orden por remitente, el segundo
    # (ej. la respuesta "1" a un menú) se procesaría antes.
    service, accounting, _ = make_service(deepseek=FakeDeepSeek({"primero": 0.2}))

    async def scenario():
        service.accept(webhook("primero", "M1"))
        service.accept(webhook("segundo", "M2"))
        service.accept(webhook("otro remitente", "M3", phone="888"))
        await service.wait_idle()

    asyncio.run(scenario())
    order_999 = [commands for phone, commands in accounting.calls if phone == "999"]
    assert order_999 == [["primero"], ["segundo"]]
    assert accounting.calls[0] == ("888", ["otro remitente"])   # otros remitentes no esperan


def test_message_without_commands_still_reaches_accounting():
    """Así un mensaje cualquiera cancela los menús pendientes."""
    service, accounting, sent = make_service()

    async def scenario():
        service.accept(webhook("jajaja ok"))
        await service.wait_idle()

    asyncio.run(scenario())
    assert accounting.calls == [("999", [])]
    assert sent == ["sin comandos"]


def test_own_messages_are_ignored_without_processing():
    service, accounting, _ = make_service()
    body = webhook("eco del bot")
    body["data"]["key"]["fromMe"] = True

    async def scenario():
        assert service.accept(body) == "ignored"
        await service.wait_idle()

    asyncio.run(scenario())
    assert accounting.calls == []


def test_webhook_endpoint_and_status_endpoint():
    from whatsapp.whatsapp_controller import create_whatsapp_router

    service, _, _ = make_service(FakeAccounting(delay=0.2))
    app = FastAPI()
    app.include_router(create_whatsapp_router(service))
    with TestClient(app) as client:
        started = time.monotonic()
        assert client.post("/whatsapp/messages-upsert", json=webhook("gasto 1 pan", "W1")).json() == {
            "status": "received"}
        assert time.monotonic() - started < 0.15
        assert client.get("/whatsapp/messages/W1/status").json() == {"status": "processing"}
        for _ in range(100):
            if client.get("/whatsapp/messages/W1/status").json()["status"] == "done":
                break
            time.sleep(0.02)
        assert client.get("/whatsapp/messages/W1/status").json() == {"status": "done"}
        assert client.get("/whatsapp/messages/NOPE/status").json() == {"status": "unknown"}
