"""E2E: el webhook responde de inmediato y procesa en segundo plano."""
import time

import httpx

from e2e_support import BOT_URL, BotUser, Run, last_mock_id, menu_options


def status(message_id: str) -> str:
    return httpx.get(f"{BOT_URL}/whatsapp/messages/{message_id}/status").json()["status"]


def test_webhook_responde_de_inmediato(run: Run, admin: BotUser):
    admin.send("hoja 01-08-2026")
    since = last_mock_id()
    started = time.monotonic()
    message_id, body = admin.post(
        "gasto 1 a, gasto 2 b, gasto 3 c, gasto 4 d, gasto 5 e, gasto 6 f, gasto 7 g y gasto 8 h")
    elapsed = time.monotonic() - started
    assert body == {"status": "received"}
    assert elapsed < 1.0, f"el webhook tardó {elapsed:.2f}s"    # DeepSeek + Sheets tardan mucho más
    assert status(message_id) == "processing"

    admin.wait_done(message_id)
    assert len(admin.replies_since(since)) == 8
    assert run.google.column(run.planilla("01-08-2026"), "B11:B18") == [1, 2, 3, 4, 5, 6, 7, 8]


def test_mensaje_reenviado_por_evolution_se_procesa_una_sola_vez(run: Run, admin: BotUser):
    admin.send("hoja 02-08-2026")
    since = last_mock_id()
    message_id, first = admin.post("gasto 777 duplicado")
    _, second = admin.post("gasto 777 duplicado", message_id=message_id)   # mismo id
    assert first == {"status": "received"} and second == {"status": "duplicate"}
    admin.wait_done(message_id)
    _, third = admin.post("gasto 777 duplicado", message_id=message_id)    # ya procesado
    assert third == {"status": "duplicate"}

    assert admin.replies_since(since) == ["Gasto registrado: $777 - duplicado"]
    assert run.google.values(run.planilla("02-08-2026"), "A11:B12")[0] == [["duplicado", 777]]


def test_respuesta_al_menu_enviada_sin_esperar_se_procesa_en_orden(run: Run, admin: BotUser):
    """El "1" llega mientras el mensaje que crea el menú aún se procesa."""
    admin.send("hoja 03-08-2026")
    admin.send("trabajador 100 orden norte y trabajador 100 orden sur")
    since = last_mock_id()
    first_id, _ = admin.post("trabajador 500 orden")
    second_id, _ = admin.post("1")                    # sin esperar al primero
    admin.wait_done(first_id)
    admin.wait_done(second_id)

    replies = admin.replies_since(since)
    assert replies[0] == "Préstamo registrado: $500 - orden"
    chosen = next(name for name, number in menu_options(replies[1]).items() if number == 1)
    assert replies[2] == f"📄 Préstamo guardado en el archivo de '{chosen}'."
    assert run.google.column(run.worker(chosen), "principal!B13:B14") == [100, 500]
