"""E2E: casos generales (registro, mensajes sin comando, lenguaje natural, /auth)."""
import os

import httpx

from e2e_support import BOT_URL, BotUser, Run, today_str


def test_numero_no_registrado_recibe_su_identificador():
    stranger = BotUser("5550000000123", "Desconocido")
    replies = stranger.send("gasto 1000 pan")
    assert len(replies) == 1
    assert "no está registrado" in replies[0] and "Tu identificador es: 5550000000123" in replies[0]


def test_mensaje_sin_comandos(admin: BotUser):
    assert admin.send("jajaja ok gracias") == [
        "🤔 No encontré ningún comando en tu mensaje. Escribe 'instrucciones' para ver lo que puedo hacer."]


def test_comando_sin_planilla_activa(admin: BotUser):
    assert admin.send("gasto 1000 pan") == [
        "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."]


def test_instrucciones(run: Run, admin: BotUser):
    help_text = admin.send("hola, ¿cómo funciona esto?")[0]
    assert help_text.startswith(f"Bienvenido al Bot de Contabilidad de {run.business_name}.")
    for command in ("gasto", "limpieza", "alimentacion", "trabajador", "nomina", "administrador",
                    "retiro", "inversion", "saldo", "efectivo", "terminar_dia", "deshacer"):
        assert command in help_text


def test_lenguaje_natural_hoja_de_hoy_y_varios_gastos(run: Run, admin: BotUser):
    today = today_str()
    replies = admin.send("Pon la hoja de hoy y anota que compré pan por 5.000 y leche por 3 mil")
    assert replies[0].endswith(f"Planilla '{today}' seleccionada.")
    assert replies[1:] == ["Gasto registrado: $5.000 - pan", "Gasto registrado: $3.000 - leche"]
    sheet = run.planilla(today)
    assert run.google.values(sheet, "A11:B12")[0] == [["pan", 5000], ["leche", 3000]]
    assert run.google.entered_type(sheet, "B11") == "numberValue"


def test_auth_protegido_con_usuario_y_clave():
    password = os.environ.get("AUTH_ADMIN_PASSWORD", "")
    assert password, "configura AUTH_ADMIN_PASSWORD en el .env"
    user = os.environ.get("AUTH_ADMIN_USER", "admin")
    for path in ("/auth/login", "/auth/status"):
        assert httpx.get(BOT_URL + path).status_code == 401
        assert httpx.get(BOT_URL + path, auth=(user, "incorrecta")).status_code == 401
    login = httpx.get(BOT_URL + "/auth/login", auth=(user, password), follow_redirects=False)
    assert login.status_code == 307
    assert login.headers["location"].startswith("https://accounts.google.com/")
    status = httpx.get(BOT_URL + "/auth/status", auth=(user, password))
    assert status.json()["authenticated"] is True
    callback = httpx.get(BOT_URL + "/auth/callback", params={"code": "x", "state": "inventado"})
    assert callback.status_code == 400
