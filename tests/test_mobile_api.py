"""API de la app (/app) de punta a punta: SQLite real, Google Sheets/Drive falsos y DeepSeek falso."""
import asyncio
from dataclasses import dataclass

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from accounting import AccountingService, CommandDispatcher, SessionManager, build_default_commands
from config.settings import PROJECT_ROOT
from database import AppRepository, BusinessRepository, Database
from mobile import AppAuthService, TokenService, create_mobile_api, install_mobile_api
from whatsapp.whatsapp_service import WhatsAppService

from fakes import SHEET_MIME, FakeDrive, FakeSheetsClient, FakeSheetsService, col_values

SECRET = "clave-de-pruebas-" + "x" * 40
BOT_NUMBER = "573001112233"


class FakeAI:
    """DeepSeek falso: respuestas fijas por texto; si no hay, devuelve el texto tal cual."""

    def __init__(self):
        self.calls: list[str] = []
        self.answers: dict[str, list[str]] = {}

    async def __call__(self, text: str) -> list[str]:
        self.calls.append(text)
        return self.answers.get(text, [text.lower()])


@dataclass
class Env:
    client: TestClient
    db: Database
    businesses: BusinessRepository
    accounting: AccountingService
    auth: AppAuthService
    service: FakeSheetsService
    drive: FakeDrive
    ai: FakeAI
    business_id: int

    def login(self, phone: str = "999", device: str = "Teléfono de prueba") -> dict:
        start = self.client.post("/app/auth/vinculaciones", json={"dispositivo": device})
        assert start.status_code == 201, start.text
        reply = self.auth.handle_whatsapp_text(phone, start.json()["mensaje"])
        assert reply.startswith("✅"), reply
        poll = self.client.get(f"/app/auth/vinculaciones/{start.json()['vinculacion_id']}")
        assert poll.json()["estado"] == "confirmada", poll.text
        return poll.json()["sesion"]

    def headers(self, phone: str = "999") -> dict:
        return {"Authorization": f"Bearer {self.login(phone)['access_token']}"}

    def create(self, headers, fecha="24-11-2026", hoja=1):
        response = self.client.post("/app/planillas", json={"fecha": fecha, "hoja": hoja}, headers=headers)
        assert response.status_code == 200, response.text
        return response.json()

    def send(self, headers, sheet_id, texto, comando=None, client_id=None):
        client_id = client_id or f"cid-{len(self.ai.calls)}-{texto}".replace(" ", "_")[:60]
        client_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in client_id).ljust(8, "_")
        response = self.client.post(
            f"/app/planillas/{sheet_id}/mensajes",
            json={"client_id": client_id, "comando": comando, "texto": texto},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        return response.json()


def build_env(tmp_path, secret=SECRET) -> Env:
    db = Database(tmp_path / "bot.db", PROJECT_ROOT / "db.sql")
    businesses = BusinessRepository(db)
    business = businesses.create_business("Panadería Prueba", "folder-planillas", "folder-trabajadores")
    businesses.create_administrator(business.id, "Marta", "999")
    businesses.create_administrator(business.id, "Luis", "998")
    other = businesses.create_business("Otro negocio", "folder-otro", None)
    businesses.create_administrator(other.id, "Pedro", "777")

    service = FakeSheetsService()
    sheets = FakeSheetsClient(service)
    drive = FakeDrive(service)
    dispatcher = CommandDispatcher(build_default_commands())
    accounting = AccountingService(dispatcher, businesses, SessionManager(), sheets, drive)
    auth = AppAuthService(AppRepository(db), businesses, TokenService(secret), BOT_NUMBER)
    ai = FakeAI()
    api = create_mobile_api(
        auth=auth, accounting=accounting, dispatcher=dispatcher, businesses=businesses,
        sheets=sheets, drive=drive, extract_commands=ai, bot_whatsapp_number=BOT_NUMBER,
        today=lambda: "24-11-2026",
    )
    app = FastAPI()
    install_mobile_api(app, api)
    return Env(TestClient(app), db, businesses, accounting, auth, service, drive, ai, business.id)


@pytest.fixture
def env(tmp_path):
    environment = build_env(tmp_path)
    with environment.client:
        yield environment


# ----------------------------------------------------------------------
# Vinculación y sesiones
# ----------------------------------------------------------------------
def test_pairing_delivers_the_session_only_once(env):
    start = env.client.post("/app/auth/vinculaciones", json={"dispositivo": "iPhone de Marta"}).json()
    assert len(start["codigo"]) == 6 and start["mensaje"] == f"VINCULAR {start['codigo']}"
    assert start["whatsapp_url"] == f"https://wa.me/{BOT_NUMBER}?text=VINCULAR%20{start['codigo']}"

    poll_url = f"/app/auth/vinculaciones/{start['vinculacion_id']}"
    assert env.client.get(poll_url).json() == {"estado": "pendiente", "sesion": None}

    reply = env.auth.handle_whatsapp_text("999", f"vincular {start['codigo']}")
    assert "App vinculada en iPhone de Marta para Panadería Prueba" in reply

    first = env.client.get(poll_url).json()
    assert first["estado"] == "confirmada"
    assert first["sesion"]["perfil"]["administrador"]["nombre"] == "Marta"
    assert first["sesion"]["perfil"]["negocio"]["nombre"] == "Panadería Prueba"
    assert env.client.get(poll_url).json() == {"estado": "consumida", "sesion": None}


def test_pairing_with_wrong_code_or_unregistered_number(env):
    env.client.post("/app/auth/vinculaciones")
    assert "no es válido o ya venció" in env.auth.handle_whatsapp_text("999", "VINCULAR 000000")
    start = env.client.post("/app/auth/vinculaciones").json()
    reply = env.auth.handle_whatsapp_text("12345", start["mensaje"])
    assert "Tu identificador es: 12345" in reply
    assert env.auth.handle_whatsapp_text("999", "gasto 5000 pan") is None   # no es para la app
    assert env.client.get("/app/auth/vinculaciones/no-existe-este-id-0000").status_code == 404


def test_expired_pairing_code_cannot_be_confirmed(env):
    start = env.client.post("/app/auth/vinculaciones").json()
    env.auth._clock = lambda: __import__("time").time() + 6 * 60
    assert "ya venció" in env.auth.handle_whatsapp_text("999", start["mensaje"])
    assert env.client.get(f"/app/auth/vinculaciones/{start['vinculacion_id']}").json()["estado"] == "expirada"


def test_refresh_rotates_and_the_old_token_stops_working(env):
    session = env.login()
    renewed = env.client.post("/app/auth/refresh", json={"refresh_token": session["refresh_token"]})
    assert renewed.status_code == 200
    assert renewed.json()["refresh_token"] != session["refresh_token"]
    again = env.client.post("/app/auth/refresh", json={"refresh_token": session["refresh_token"]})
    assert again.status_code == 401 and again.json()["codigo"] == "SESION_TERMINADA"

    headers = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    assert env.client.get("/app/perfil", headers=headers).status_code == 200


def test_logout_and_cerrar_app_cut_access_immediately(env):
    session = env.login()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    assert env.client.post("/app/auth/logout", json={"refresh_token": session["refresh_token"]}).status_code == 204
    assert env.client.get("/app/perfil", headers=headers).json()["codigo"] == "SESION_TERMINADA"

    other = env.headers()
    another = env.headers()
    assert env.auth.handle_whatsapp_text("999", "cerrar app") == "✅ Se cerró la app en 2 dispositivo(s)."
    assert env.client.get("/app/perfil", headers=other).status_code == 401
    assert env.client.get("/app/perfil", headers=another).status_code == 401


def test_deactivated_administrator_is_logged_out(env):
    headers = env.headers()
    connection = env.db.connect()
    connection.execute("UPDATE business_administrators SET state = 'inactive' WHERE phone_number = '999'")
    connection.commit()
    response = env.client.get("/app/perfil", headers=headers)
    assert response.status_code == 401 and response.json()["codigo"] == "USUARIO_INACTIVO"


def test_token_is_required(env):
    response = env.client.get("/app/perfil")
    assert response.status_code == 401
    assert response.json() == {"detail": "Falta el token de acceso.", "codigo": "TOKEN_INVALIDO"}
    bad = env.client.get("/app/perfil", headers={"Authorization": "Bearer no.es.un.jwt"})
    assert bad.status_code == 401 and bad.json()["codigo"] == "TOKEN_INVALIDO"


def test_api_is_disabled_without_secret(tmp_path):
    environment = build_env(tmp_path, secret="")
    with environment.client:
        response = environment.client.post("/app/auth/vinculaciones")
    assert response.status_code == 503 and response.json()["codigo"] == "APP_DESHABILITADA"
    assert "no está habilitada" in environment.auth.handle_whatsapp_text("999", "VINCULAR 123456")


# ----------------------------------------------------------------------
# Perfil y comandos
# ----------------------------------------------------------------------
def test_profile_and_renames(env):
    headers = env.headers()
    profile = env.client.get("/app/perfil", headers=headers).json()
    assert profile["administrador"] == {"id": 1, "nombre": "Marta", "identificador": "999"}
    assert profile["negocio"]["carpeta_planillas_url"] == "https://drive.google.com/drive/folders/folder-planillas"
    assert [(a["nombre"], a["es_usted"]) for a in profile["administradores"]] == [("Marta", True), ("Luis", False)]
    assert profile["google_conectado"] is True and profile["whatsapp_bot"] == BOT_NUMBER

    renamed = env.client.patch("/app/negocio", json={"nombre": "  Panadería   La Espiga "}, headers=headers)
    assert renamed.json()["negocio"]["nombre"] == "Panadería La Espiga"
    renamed = env.client.patch("/app/administrador", json={"nombre": "Marta Gómez"}, headers=headers)
    assert renamed.json()["administrador"]["nombre"] == "Marta Gómez"
    invalid = env.client.patch("/app/negocio", json={"nombre": "x"}, headers=headers)
    assert invalid.status_code == 422 and invalid.json()["codigo"] == "NOMBRE_INVALIDO"


def test_commands_catalog_includes_aliases(env):
    commands = env.client.get("/app/comandos", headers=env.headers()).json()
    assert [c["id"] for c in commands][:4] == ["gasto", "efectivo", "saldo", "trabajador"]
    prestamo = next(c for c in commands if c["id"] == "trabajador")
    assert prestamo["etiqueta"] == "Préstamo" and prestamo["sugiere_trabajador"] is True
    assert "t" in prestamo["alias"]
    assert next(c for c in commands if c["id"] == "deshacer")["confirmar"] is True


# ----------------------------------------------------------------------
# Planillas
# ----------------------------------------------------------------------
def test_create_planillas_in_order_and_list_them(env):
    headers = env.headers()
    early = env.client.post("/app/planillas", json={"fecha": "24-11-2026", "hoja": 2}, headers=headers)
    assert early.status_code == 422
    assert early.json()["detail"] == "No existe la planilla '24-11-2026'. Las planillas adicionales se crean en orden."

    first = env.create(headers, "24-11-2026", 1)
    assert first["creada"] is True and first["planilla"]["nombre"] == "24-11-2026"
    assert first["mensajes"][0]["tipo"] == "aviso"        # no hay planilla del día anterior
    assert env.create(headers, "24-11-2026", 1)["creada"] is False
    second = env.create(headers, "24-11-2026", 2)
    assert second["planilla"] == {**second["planilla"], "nombre": "24-11-2026-2", "hoja": 2}
    env.create(headers, "23-11-2026", 1)
    env.create(headers, "30-10-2026", 1)

    months = env.client.get("/app/planillas/meses", headers=headers).json()
    assert [(m["etiqueta"], m["carpeta"]) for m in months] == [
        ("Noviembre 2026", "noviembre-2026"), ("Octubre 2026", "octubre-2026")]
    november = env.client.get("/app/planillas?anio=2026&mes=11", headers=headers).json()
    assert [p["nombre"] for p in november] == ["24-11-2026", "24-11-2026-2", "23-11-2026"]
    assert env.client.get("/app/planillas?anio=2026&mes=9", headers=headers).json() == []
    bad_date = env.client.post("/app/planillas", json={"fecha": "2026-11-24"}, headers=headers)
    assert bad_date.status_code == 422 and bad_date.json()["codigo"] == "FECHA_INVALIDA"


def test_creating_a_planilla_does_not_touch_the_chat_conversation(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    env.drive.add_worker("jose salon")
    env.drive.add_worker("jose panadero")
    env.send(headers, sheet, "20.000 jose", comando="trabajador")
    env.create(headers, "25-11-2026", 1)          # no debe cancelar la pregunta pendiente
    state = env.client.get(f"/app/planillas/{sheet}/estado", headers=headers).json()
    assert state["seleccion"] is not None


def test_today_card(env):
    headers = env.headers()
    empty = env.client.get("/app/planillas/hoy", headers=headers).json()
    assert empty == {"fecha": "24-11-2026", "planillas": [], "ultima": None, "totales": None}

    sheet = env.create(headers)["planilla"]["id"]
    env.send(headers, sheet, "200.000", comando="efectivo")
    env.send(headers, sheet, "5.000 pan", comando="gasto")
    env.create(headers, "24-11-2026", 2)
    today = env.client.get("/app/planillas/hoy", headers=headers).json()
    assert [p["hoja"] for p in today["planillas"]] == [1, 2]
    assert today["ultima"]["nombre"] == "24-11-2026-2"
    assert today["totales"]["saldo_previo"] == 200000          # B42 de la hoja 2 = B58 de la hoja 1


def test_overview_counts_rows_per_section(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    for text in ("1.000 pan", "2.000 leche", "3.000 huevos"):
        env.send(headers, sheet, text, comando="gasto")
    env.send(headers, sheet, "100.000", comando="efectivo")
    summary = env.client.get(f"/app/planillas/{sheet}/resumen", headers=headers).json()
    sections = {s["id"]: (s["usadas"], s["capacidad"]) for s in summary["secciones"]}
    assert sections["compras"] == (3, 24) and sections["aseo"] == (0, 8)
    assert summary["totales"]["gastos"] == 6000 and summary["totales"]["efectivo"] == 100000
    assert summary["planilla"]["nombre"] == "24-11-2026"


def test_planillas_of_another_business_are_not_found(env):
    sheet = env.create(env.headers())["planilla"]["id"]
    env.drive.foreign["ajena-123"] = {"id": "ajena-123", "name": "24-11-2026", "mimeType": SHEET_MIME,
                                      "trashed": False, "parents": ["month:otro"]}
    outsider = env.headers("777")
    for path in (f"/app/planillas/{sheet}", f"/app/planillas/{sheet}/resumen",
                 f"/app/planillas/{sheet}/estado", "/app/planillas/ajena-123"):
        response = env.client.get(path, headers=outsider)
        assert response.status_code == 404 and response.json()["codigo"] == "PLANILLA_NO_EXISTE", path
    response = env.client.post(f"/app/planillas/{sheet}/mensajes", headers=outsider,
                               json={"client_id": "intruso-1", "comando": "gasto", "texto": "1000 robo"})
    assert response.status_code == 404
    assert col_values(env.service, sheet, "A11:B12") == []


def test_google_not_connected(env):
    headers = env.headers()
    env.drive.service = None
    response = env.client.get("/app/planillas/meses", headers=headers)
    assert response.status_code == 503 and response.json()["codigo"] == "GOOGLE_NO_CONECTADO"
    assert env.client.get("/app/perfil", headers=headers).json()["google_conectado"] is False


# ----------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------
def test_well_written_command_skips_deepseek(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    result = env.send(headers, sheet, "5.000 pan", comando="gasto")
    assert result["respuestas"] == [{"tipo": "exito", "texto": "Gasto registrado: $5.000 - pan"}]
    assert result["comandos"] == ["gasto 5000 pan"] and result["interpretado_por_ia"] is False
    assert result["estado"] == {"seleccion": None, "deshacer": "gasto 5000 pan"}
    assert env.ai.calls == []
    assert col_values(env.service, sheet, "A11:B11") == [["pan", 5000]]


def test_natural_language_goes_through_deepseek(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    env.ai.answers["gasto 5 mil de pan"] = ["gasto 5000 pan"]
    result = env.send(headers, sheet, "5 mil de pan", comando="gasto")
    assert env.ai.calls == ["gasto 5 mil de pan"]
    assert result["interpretado_por_ia"] is True and result["comandos"] == ["gasto 5000 pan"]

    env.ai.answers["gasto 3000 leche y aseo 2000"] = ["gasto 3000 leche", "limpieza 2000"]
    free = env.send(headers, sheet, "gasto 3000 leche y aseo 2000")       # chip "Libre"
    assert [r["texto"] for r in free["respuestas"]] == [
        "Gasto registrado: $3.000 - leche", "Gasto de limpieza registrado: $2.000"]


def test_repeated_client_id_does_not_register_twice(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    first = env.send(headers, sheet, "5.000 pan", comando="gasto", client_id="mismo-id-1")
    second = env.send(headers, sheet, "5.000 pan", comando="gasto", client_id="mismo-id-1")
    assert first == second
    assert col_values(env.service, sheet, "A11:B12") == [["pan", 5000]]


def test_sheet_change_commands_are_rejected_in_the_chat(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    env.ai.answers["pon la hoja del 25 y gasto 1000 pan"] = ["hoja 25-11-2026", "gasto 1000 pan"]
    result = env.send(headers, sheet, "pon la hoja del 25 y gasto 1000 pan")
    assert result["comandos"] == ["gasto 1000 pan"]
    assert result["respuestas"][-1]["tipo"] == "aviso"
    assert "Para cambiar de planilla usa la pantalla Planillas" in result["respuestas"][-1]["texto"]
    assert "25-11-2026" not in env.drive.planillas
    assert col_values(env.service, sheet, "A11:B11") == [["pan", 1000]]


def test_missing_text_or_unknown_command(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    response = env.client.post(f"/app/planillas/{sheet}/mensajes", headers=headers,
                               json={"client_id": "vacio-001", "comando": "gasto", "texto": "  "})
    assert response.status_code == 422 and response.json()["codigo"] == "FALTA_TEXTO"
    response = env.client.post(f"/app/planillas/{sheet}/mensajes", headers=headers,
                               json={"client_id": "raro-0001", "comando": "hoja", "texto": "x"})
    assert response.status_code == 422 and response.json()["codigo"] == "COMANDO_DESCONOCIDO"
    response = env.client.post(f"/app/planillas/{sheet}/mensajes", headers=headers,
                               json={"client_id": "x", "texto": "hola"})
    assert response.status_code == 422 and response.json()["codigo"] == "DATOS_INVALIDOS"


def test_worker_question_as_buttons_answer_and_cancel(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    salon = env.drive.add_worker("jose salon")
    env.drive.add_worker("jose panadero")

    result = env.send(headers, sheet, "20.000 jose", comando="trabajador")
    assert [r["tipo"] for r in result["respuestas"]] == ["exito", "seleccion"]
    assert result["respuestas"][1]["texto"] == "Hay varios trabajadores con nombre similar a 'jose'"
    question = result["estado"]["seleccion"]
    assert question["opciones"] == [
        {"valor": 1, "etiqueta": "jose salon", "crea": False},
        {"valor": 2, "etiqueta": "jose panadero", "crea": False},
        {"valor": 3, "etiqueta": "Crear nuevo trabajador 'jose'", "crea": True},
    ]
    assert question["comando"] == "trabajador 20000 jose"
    assert question["planilla_id"] == sheet
    assert env.client.get(f"/app/planillas/{sheet}/estado", headers=headers).json()["seleccion"] == question

    invalid = env.client.post(f"/app/planillas/{sheet}/seleccion", json={"opcion": 9}, headers=headers)
    assert invalid.status_code == 422 and invalid.json()["codigo"] == "OPCION_INVALIDA"
    answered = env.client.post(f"/app/planillas/{sheet}/seleccion", json={"opcion": 1}, headers=headers).json()
    assert answered["respuestas"] == [{"tipo": "exito", "texto": "Préstamo guardado en el archivo de 'jose salon'."}]
    assert answered["estado"]["seleccion"] is None
    assert col_values(env.service, salon, "principal!A13:B13") == [["24-11-2026", 20000]]

    env.send(headers, sheet, "15.000 jose", comando="trabajador")
    cancelled = env.client.delete(f"/app/planillas/{sheet}/seleccion", headers=headers).json()
    assert cancelled["respuestas"][0]["tipo"] == "aviso"
    assert "se canceló 'trabajador 15000 jose' y se borró de la planilla" in cancelled["respuestas"][0]["texto"]
    assert col_values(env.service, sheet, "C11:D12") == [["jose", 20000]]
    nothing = env.client.delete(f"/app/planillas/{sheet}/seleccion", headers=headers)
    assert nothing.status_code == 409 and nothing.json()["codigo"] == "SIN_PREGUNTA"


def test_app_and_whatsapp_sessions_are_separate(env):
    headers = env.headers()
    sheet = env.create(headers)["planilla"]["id"]
    env.send(headers, sheet, "5.000 pan", comando="gasto")

    # Por WhatsApp no hay nada que deshacer: lo del app es de otro canal.
    assert env.accounting.handle_commands("999", ["deshacer"]) == ["⚠️ No hay un comando para deshacer."]
    assert col_values(env.service, sheet, "A11:B11") == [["pan", 5000]]

    undo = env.send(headers, sheet, "", comando="deshacer")
    assert undo["respuestas"] == [{"tipo": "exito", "texto": "Se deshizo: gasto 5000 pan."}]
    assert col_values(env.service, sheet, "A11:B11") == []


def test_two_admins_write_to_the_same_planilla(env):
    marta, luis = env.headers("999"), env.headers("998")
    sheet = env.create(marta)["planilla"]["id"]
    env.send(marta, sheet, "1.000 pan", comando="gasto")
    env.send(luis, sheet, "2.000 leche", comando="gasto")
    env.send(marta, sheet, "", comando="deshacer")          # solo lo de Marta
    assert col_values(env.service, sheet, "A11:B12") == [["leche", 2000]]


# ----------------------------------------------------------------------
# Trabajadores
# ----------------------------------------------------------------------
def test_workers_list_detail_and_archived_payroll(env):
    headers = env.headers()
    assert env.client.get("/app/trabajadores", headers=headers).json() == {
        "carpeta_configurada": True, "trabajadores": []}

    sheet = env.create(headers)["planilla"]["id"]
    env.send(headers, sheet, "20.000 juan", comando="trabajador")
    env.send(headers, sheet, "5.000 juan", comando="trabajador")
    env.drive.add_worker("Ana María")
    workers = env.client.get("/app/trabajadores", headers=headers).json()["trabajadores"]
    assert [w["nombre"] for w in workers] == ["Ana María", "juan"]
    juan = next(w for w in workers if w["nombre"] == "juan")["id"]

    detail = env.client.get(f"/app/trabajadores/{juan}", headers=headers).json()
    assert [(v["fila"], v["fecha"], v["monto"]) for v in detail["vales"]] == [
        (13, "24-11-2026", 20000), (14, "24-11-2026", 5000)]
    assert (detail["usados"], detail["capacidad"], detail["total_prestamos"]) == (2, 16, 25000)
    assert detail["nominas"] == []

    env.send(headers, sheet, "100.000 juan", comando="nomina")
    detail = env.client.get(f"/app/trabajadores/{juan}", headers=headers).json()
    assert detail["vales"] == [] and detail["usados"] == 0
    assert len(detail["nominas"]) == 1
    archived = detail["nominas"][0]

    # Google ajusta las fórmulas al borrar filas; el Sheets falso no, así que se imita.
    book = env.service.files[juan]
    book.sheets[archived["titulo"]]["cells"][(2, 21)] = "=SUM(B4:B20)"
    nomina = env.client.get(f"/app/trabajadores/{juan}/nominas/{archived['hoja_id']}", headers=headers).json()
    assert [(v["fecha"], v["monto"]) for v in nomina["vales"]] == [("24-11-2026", 20000), ("24-11-2026", 5000)]
    assert nomina["total_prestamos"] == 25000
    assert nomina["url"].endswith(f"#gid={archived['hoja_id']}")

    principal = next(gid for title, s in book.sheets.items() if title == "principal" for gid in [s["id"]])
    response = env.client.get(f"/app/trabajadores/{juan}/nominas/{principal}", headers=headers)
    assert response.status_code == 404


def test_worker_of_another_business_is_not_found(env):
    juan = env.drive.add_worker("juan")
    outsider = env.headers("777")
    assert env.client.get("/app/trabajadores", headers=outsider).json() == {
        "carpeta_configurada": False, "trabajadores": []}
    assert env.client.get(f"/app/trabajadores/{juan}", headers=outsider).status_code == 404


# ----------------------------------------------------------------------
# WhatsApp: los mensajes de vinculación no pasan por DeepSeek ni por la contabilidad
# ----------------------------------------------------------------------
def test_whatsapp_answers_pairing_messages_directly(env):
    class NoAccounting:
        def handle_commands(self, *_):
            raise AssertionError("no debía llegar a la contabilidad")

        def has_pending_selection(self, *_):
            return False

    class NoDeepSeek:
        async def extract_commands(self, _text):
            raise AssertionError("no debía llegar a DeepSeek")

    whatsapp = WhatsAppService("http://evo", "inst", "tok", None, NoDeepSeek(), NoAccounting(), app_auth=env.auth)
    sent = []

    async def fake_send(to, message):
        sent.append(message)

    whatsapp.send_message = fake_send
    start = env.client.post("/app/auth/vinculaciones").json()
    body = {"data": {"key": {"remoteJid": "999@s.whatsapp.net", "id": "PAIR1"},
                     "messageType": "conversation", "message": {"conversation": start["mensaje"]}}}

    async def scenario():
        assert whatsapp.accept(body) == "received"
        await whatsapp.wait_idle()

    asyncio.run(scenario())
    assert sent and sent[0].startswith("✅ App vinculada")
    poll = env.client.get(f"/app/auth/vinculaciones/{start['vinculacion_id']}").json()
    assert poll["estado"] == "confirmada"
