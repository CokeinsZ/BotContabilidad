"""E2E de la API de la app móvil (/app): bot local + Google Drive/Sheets y DeepSeek reales.

La app se vincula como en la vida real: pide un código y el administrador se
lo envía al bot por el webhook de WhatsApp ("VINCULAR 482913").

Cada prueba usa un negocio propio (con su carpeta de planillas), así los
listados de meses y planillas no dependen de las demás pruebas. La carpeta de
trabajadores sí es compartida por toda la corrida: los trabajadores de aquí se
llaman "wilmer app …", "yesid app" y "zoila app" para no coincidir con las
búsquedas de test_e2e_trabajadores.py (que buscan por "contiene").
"""
import uuid
from dataclasses import dataclass

import httpx
import pytest

from e2e_support import BOT_URL, AppClient, BotUser, Run, today_str


@dataclass
class Negocio:
    id: int
    folder: str
    name: str


@pytest.fixture
def negocio(run: Run, request) -> Negocio:
    label = "app-" + request.node.name.removeprefix("test_")[:24]
    business_id, folder = run.new_business(label)
    return Negocio(business_id, folder, f"E2E {label} {run.stamp}")


@pytest.fixture
def app_admin(run: Run, negocio: Negocio) -> BotUser:
    return run.new_admin("Admin App", negocio.id)


@pytest.fixture
def app(app_admin: BotUser) -> AppClient:
    return AppClient.pair(app_admin)


def status_and_code(response: httpx.Response) -> tuple[int, str | None]:
    body = response.json() if response.content else {}
    return response.status_code, body.get("codigo")


# ----------------------------------------------------------------------
# Vinculación y sesiones
# ----------------------------------------------------------------------
def test_vinculacion_por_whatsapp_y_sesiones(run: Run, negocio: Negocio):
    admin = run.new_admin("Admin Vinculación", negocio.id)
    start = httpx.post(f"{BOT_URL}/app/auth/vinculaciones", json={"dispositivo": "Celular E2E"}).json()
    assert start["mensaje"] == f"VINCULAR {start['codigo']}"
    assert start["whatsapp_url"].startswith("https://wa.me/")
    poll_url = f"{BOT_URL}/app/auth/vinculaciones/{start['vinculacion_id']}"
    assert httpx.get(poll_url).json() == {"estado": "pendiente", "sesion": None}

    replies = admin.send(start["mensaje"])
    assert replies == [
        f"✅ App vinculada en Celular E2E para {negocio.name}.\n"
        "Si no fuiste tú, escribe 'cerrar app' para desconectarla."
    ]
    first = httpx.get(poll_url).json()
    assert first["estado"] == "confirmada"
    assert httpx.get(poll_url).json() == {"estado": "consumida", "sesion": None}

    app = AppClient(admin, first["sesion"])
    profile = app.ok("GET", "/perfil")
    assert profile["administrador"]["nombre"] == "Admin Vinculación"
    assert profile["administrador"]["identificador"] == admin.phone
    assert profile["negocio"]["nombre"] == negocio.name
    assert profile["google_conectado"] is True
    assert profile["hoy"] == today_str()

    # El refresh rota: el anterior deja de servir.
    renewed = httpx.post(f"{BOT_URL}/app/auth/refresh", json={"refresh_token": app.refresh_token})
    assert renewed.status_code == 200
    old = httpx.post(f"{BOT_URL}/app/auth/refresh", json={"refresh_token": app.refresh_token})
    assert status_and_code(old) == (401, "SESION_TERMINADA")

    # Cerrar sesión corta el acceso al instante (no espera a que venza el JWT).
    renewed_access = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    assert httpx.get(f"{BOT_URL}/app/perfil", headers=renewed_access).status_code == 200
    logout = httpx.post(f"{BOT_URL}/app/auth/logout", json={"refresh_token": renewed.json()["refresh_token"]})
    assert logout.status_code == 204
    assert status_and_code(httpx.get(f"{BOT_URL}/app/perfil", headers=renewed_access)) == (401, "SESION_TERMINADA")

    # "cerrar app" por WhatsApp cierra la app en todos los dispositivos.
    other = AppClient.pair(admin, device="Tablet E2E")
    assert admin.send("cerrar app") == ["✅ Se cerró la app en 1 dispositivo(s)."]
    assert other.get("/perfil").status_code == 401
    assert admin.send("cerrar app") == ["No tenías la app abierta en ningún dispositivo."]


def test_vinculacion_con_codigo_errado_o_numero_no_registrado(run: Run, negocio: Negocio):
    admin = run.new_admin("Admin Código", negocio.id)
    assert admin.send("VINCULAR 000000") == [
        "⚠️ El código de vinculación no es válido o ya venció. Genera uno nuevo en la app."]
    stranger = BotUser("5550000000124", "Desconocido")
    replies = stranger.send("VINCULAR 123456")
    assert len(replies) == 1 and "Tu identificador es: 5550000000124" in replies[0]
    assert status_and_code(httpx.get(f"{BOT_URL}/app/perfil")) == (401, "TOKEN_INVALIDO")


# ----------------------------------------------------------------------
# Planillas
# ----------------------------------------------------------------------
def test_crear_abrir_y_listar_planillas(run: Run, negocio: Negocio, app: AppClient):
    early = app.request("POST", "/planillas", json={"fecha": "10-03-2025", "hoja": 2})
    assert early.status_code == 422
    assert early.json()["detail"] == (
        "No existe la planilla '10-03-2025'. Las planillas adicionales se crean en orden.")

    first = app.create("10-03-2025")
    assert first["creada"] is True
    assert first["mensajes"][0]["tipo"] == "aviso"
    assert "No existe una planilla para el día anterior: '09-03-2025'" in first["mensajes"][0]["texto"]
    sheet_1 = first["planilla"]["id"]
    assert run.planilla("10-03-2025", negocio.folder) == sheet_1
    assert app.create("10-03-2025") == {**first, "creada": False, "mensajes": [
        {"tipo": "exito", "texto": "Planilla '10-03-2025' seleccionada."}]}

    app.send(sheet_1, "350.000", "efectivo")
    second = app.create("10-03-2025", 2)
    assert second["planilla"]["nombre"] == "10-03-2025-2" and second["planilla"]["hoja"] == 2
    assert second["mensajes"] == [{"tipo": "exito", "texto": (
        "Planilla '10-03-2025-2' seleccionada. Saldo de caja cargado desde '10-03-2025'.")}]
    sheet_2 = second["planilla"]["id"]
    assert run.google.value(sheet_2, "B42") == 350000
    assert run.google.entered_type(sheet_2, "B42") == "numberValue"
    app.create("01-04-2025")

    assert run.google.planillas_of(negocio.folder, "marzo-2025") == ["10-03-2025", "10-03-2025-2"]
    months = app.ok("GET", "/planillas/meses")
    assert [(m["anio"], m["mes"], m["carpeta"], m["etiqueta"]) for m in months] == [
        (2025, 4, "abril-2025", "Abril 2025"), (2025, 3, "marzo-2025", "Marzo 2025")]
    march = app.ok("GET", "/planillas", params={"anio": 2025, "mes": 3})
    assert [(p["nombre"], p["hoja"]) for p in march] == [("10-03-2025", 1), ("10-03-2025-2", 2)]
    assert app.ok("GET", "/planillas", params={"anio": 2025, "mes": 5}) == []
    detail = app.ok("GET", f"/planillas/{sheet_2}")
    assert detail == {"id": sheet_2, "nombre": "10-03-2025-2", "fecha": "10-03-2025", "hoja": 2,
                      "url": f"https://docs.google.com/spreadsheets/d/{sheet_2}/edit"}


def test_tarjeta_de_hoy(run: Run, negocio: Negocio, app: AppClient):
    today = today_str()
    assert app.ok("GET", "/planillas/hoy") == {"fecha": today, "planillas": [], "ultima": None, "totales": None}

    sheet = app.create(today)["planilla"]["id"]
    app.send(sheet, "200.000", "efectivo")
    app.send(sheet, "15.000 harina", "gasto")
    card = app.ok("GET", "/planillas/hoy")
    assert [p["nombre"] for p in card["planillas"]] == [today]
    assert card["ultima"]["id"] == sheet

    cells = run.google.cells(sheet, "B38", "B39", "B40", "B42", "B58")
    assert card["totales"] == {
        "gastos": cells["B38"], "efectivo": cells["B39"], "venta_total": cells["B40"],
        "saldo_previo": cells["B42"], "saldo_total": cells["B58"],
    }
    assert (card["totales"]["gastos"], card["totales"]["efectivo"]) == (15000, 200000)


# ----------------------------------------------------------------------
# Chat
# ----------------------------------------------------------------------
def test_chat_registra_en_la_planilla_sin_deepseek(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("05-03-2025")["planilla"]["id"]

    efectivo = app.send(sheet, "350.000", "efectivo")
    assert AppClient.texts(efectivo) == ["Efectivo registrado: $350.000"]
    assert efectivo["comandos"] == ["efectivo 350000"] and efectivo["interpretado_por_ia"] is False

    gasto = app.send(sheet, "pan 5.000", "gasto")     # el monto también puede ir al final
    assert AppClient.texts(gasto) == ["Gasto registrado: $5.000 - pan"]
    assert gasto["comandos"] == ["gasto 5000 pan"] and gasto["interpretado_por_ia"] is False

    assert AppClient.texts(app.send(sheet, "2.000", "limpieza")) == ["Gasto de limpieza registrado: $2.000"]
    retiro = app.send(sheet, "100.000 banco", "retiro")
    assert AppClient.texts(retiro) == ["Retiro registrado: $100.000 - banco"]
    assert retiro["estado"] == {"seleccion": None, "deshacer": "retiro 100000 banco"}

    google = run.google
    assert google.values(sheet, "A11:B11")[0] == [["pan", 5000]]
    assert google.entered_type(sheet, "B11") == "numberValue"
    assert google.value(sheet, "B39") == 350000
    assert google.value(sheet, "E11") == 2000
    assert google.values(sheet, "C39:E39")[0] == [["banco", "", 100000]]

    summary = app.ok("GET", f"/planillas/{sheet}/resumen")
    sections = {s["id"]: (s["usadas"], s["capacidad"]) for s in summary["secciones"]}
    assert sections == {
        "compras": (1, 24), "prestamos": (0, 16), "administrador": (0, 9), "retiros": (1, 21),
        "inversiones": (0, 6), "aseo": (1, 8), "alimentacion": (0, 5),
    }
    cells = google.cells(sheet, "B38", "B39", "B40", "B42", "B58")
    assert summary["totales"] == {
        "gastos": cells["B38"], "efectivo": cells["B39"], "venta_total": cells["B40"],
        "saldo_previo": cells["B42"], "saldo_total": cells["B58"],
    }


def test_chat_en_lenguaje_natural_pasa_por_deepseek(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("06-03-2025")["planilla"]["id"]

    with_command = app.send(sheet, "5 mil de pan", "gasto")
    assert with_command["interpretado_por_ia"] is True
    assert with_command["comandos"] == ["gasto 5000 pan"]
    assert AppClient.texts(with_command) == ["Gasto registrado: $5.000 - pan"]

    free = app.send(sheet, "compré leche por 3 mil y huevos por 4 mil")      # chip "Libre"
    assert free["comandos"] == ["gasto 3000 leche", "gasto 4000 huevos"]
    assert run.google.values(sheet, "A11:B13")[0] == [["pan", 5000], ["leche", 3000], ["huevos", 4000]]


def test_chat_reintento_no_duplica_y_no_cambia_de_planilla(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("07-03-2025")["planilla"]["id"]
    client_id = f"e2e-reintento-{uuid.uuid4().hex}"
    first = app.send(sheet, "1.000 pan", "gasto", client_id=client_id)
    retry = app.send(sheet, "1.000 pan", "gasto", client_id=client_id)
    assert retry == first
    assert run.google.values(sheet, "A11:B12")[0] == [["pan", 1000]]

    result = app.send(sheet, "pon la hoja del 20-03-2025 y anota un gasto de 2000 en sal")
    assert result["comandos"] == ["gasto 2000 sal"]
    assert result["respuestas"][-1]["tipo"] == "aviso"
    assert "Para cambiar de planilla usa la pantalla Planillas" in result["respuestas"][-1]["texto"]
    assert run.google.planilla(negocio.folder, "20-03-2025") is None
    assert run.google.values(sheet, "A11:B12")[0] == [["pan", 1000], ["sal", 2000]]


def test_app_y_whatsapp_tienen_sesiones_separadas(run: Run, negocio: Negocio,
                                                   app_admin: BotUser, app: AppClient):
    sheet = app.create("08-03-2025")["planilla"]["id"]
    app.send(sheet, "1.000 harina", "gasto")

    # Por WhatsApp no hay nada que deshacer: lo de la app es de otro canal.
    assert app_admin.send("deshacer") == ["⚠️ No hay un comando para deshacer."]
    assert app_admin.send("hoja 08-03-2025") == ["Planilla '08-03-2025' seleccionada."]
    assert app_admin.send("gasto 2000 sal") == ["Gasto registrado: $2.000 - sal"]

    # Deshacer en la app revierte solo lo de la app (y viceversa).
    undo = app.send(sheet, "", "deshacer")
    assert AppClient.texts(undo) == ["Se deshizo: gasto 1000 harina."]
    assert run.google.values(sheet, "A11:B12")[0] == [["sal", 2000]]
    assert app_admin.send("deshacer") == ["✅ Se deshizo: gasto 2000 sal."]
    assert run.google.values(sheet, "A11:B11")[0] == []


def test_pregunta_de_trabajadores_como_botones(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("09-03-2025")["planilla"]["id"]
    assert AppClient.texts(app.send(sheet, "10.000 wilmer app caja", "trabajador")) == [
        "Préstamo registrado: $10.000 - wilmer app caja",
        "Se creó el archivo del trabajador 'wilmer app caja'.",
        "Préstamo guardado en el archivo de 'wilmer app caja'.",
    ]
    app.send(sheet, "20.000 wilmer app horno", "trabajador")

    asked = app.send(sheet, "5.000 wilmer app", "trabajador")
    assert [r["tipo"] for r in asked["respuestas"]] == ["exito", "seleccion"]
    question = asked["estado"]["seleccion"]
    assert question["pregunta"] == "Hay varios trabajadores con nombre similar a 'wilmer app'"
    labels = {option["etiqueta"]: option for option in question["opciones"]}
    assert set(labels) == {"wilmer app caja", "wilmer app horno", "Crear nuevo trabajador 'wilmer app'"}
    assert labels["Crear nuevo trabajador 'wilmer app'"]["crea"] is True
    assert question["planilla_id"] == sheet
    assert app.ok("GET", f"/planillas/{sheet}/estado")["seleccion"] == question

    answered = app.ok("POST", f"/planillas/{sheet}/seleccion", json={"opcion": labels["wilmer app horno"]["valor"]})
    assert AppClient.texts(answered) == ["Préstamo guardado en el archivo de 'wilmer app horno'."]
    assert answered["estado"]["seleccion"] is None
    assert run.google.column(run.worker("wilmer app horno"), "principal!B13:B14") == [20000, 5000]

    app.send(sheet, "7.000 wilmer app", "trabajador")
    cancelled = app.ok("DELETE", f"/planillas/{sheet}/seleccion")
    assert cancelled["respuestas"] == [{"tipo": "aviso", "texto": (
        "No escogiste ninguna opción del menú, así que se canceló 'trabajador 7000 wilmer app' "
        "y se borró de la planilla.")}]
    assert run.google.values(sheet, "C11:D14")[0] == [
        ["wilmer app caja", 10000], ["wilmer app horno", 20000], ["wilmer app", 5000]]
    assert status_and_code(app.request("DELETE", f"/planillas/{sheet}/seleccion")) == (409, "SIN_PREGUNTA")


# ----------------------------------------------------------------------
# Trabajadores
# ----------------------------------------------------------------------
def test_trabajador_detalle_y_nomina_archivada(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("12-03-2025")["planilla"]["id"]
    app.send(sheet, "20.000 yesid app", "trabajador")
    app.send(sheet, "5.000 yesid app", "trabajador")

    workers = app.ok("GET", "/trabajadores")
    assert workers["carpeta_configurada"] is True
    yesid = next(w["id"] for w in workers["trabajadores"] if w["nombre"] == "yesid app")
    assert yesid == run.worker("yesid app")

    detail = app.ok("GET", f"/trabajadores/{yesid}")
    assert [(v["fila"], v["fecha"], v["monto"]) for v in detail["vales"]] == [
        (13, "12-03-2025", 20000), (14, "12-03-2025", 5000)]
    assert (detail["usados"], detail["capacidad"], detail["nominas"]) == (2, 16, [])
    assert detail["total_prestamos"] == run.google.value(yesid, "principal!B30") == 25000

    payroll = app.send(sheet, "100.000 yesid app", "nomina")
    texts = AppClient.texts(payroll)
    assert texts[0] == "Pago de nómina registrado en planilla: $100.000 - yesid app"
    assert "Suma de préstamos: $25.000" in texts[1]
    today = today_str()
    assert texts[2] == f"Nómina procesada: hoja '{today}' creada y hoja principal limpiada."

    detail = app.ok("GET", f"/trabajadores/{yesid}")
    assert detail["vales"] == [] and detail["usados"] == 0
    assert [(n["titulo"], n["fecha"]) for n in detail["nominas"]] == [(today, today)]
    archived = app.ok("GET", f"/trabajadores/{yesid}/nominas/{detail['nominas'][0]['hoja_id']}")
    assert [(v["fecha"], v["monto"]) for v in archived["vales"]] == [("12-03-2025", 20000), ("12-03-2025", 5000)]
    assert archived["total_prestamos"] == 25000
    assert archived["url"].endswith(f"#gid={detail['nominas'][0]['hoja_id']}")


def test_otro_negocio_no_ve_planillas_ni_trabajadores(run: Run, negocio: Negocio, app: AppClient):
    sheet = app.create("13-03-2025")["planilla"]["id"]
    app.send(sheet, "1.000 zoila app", "trabajador")
    zoila = run.worker("zoila app")

    outsider = AppClient.pair(run.new_admin("Admin Ajeno", run.no_workers_business_id))
    for path in (f"/planillas/{sheet}", f"/planillas/{sheet}/resumen", f"/planillas/{sheet}/estado"):
        assert status_and_code(outsider.get(path)) == (404, "PLANILLA_NO_EXISTE"), path
    intrusion = outsider.request("POST", f"/planillas/{sheet}/mensajes",
                                 json={"client_id": f"e2e-{uuid.uuid4().hex}", "comando": "gasto", "texto": "1000 robo"})
    assert status_and_code(intrusion) == (404, "PLANILLA_NO_EXISTE")
    assert run.google.values(sheet, "A11:B11")[0] == []

    assert outsider.ok("GET", "/trabajadores") == {"carpeta_configurada": False, "trabajadores": []}
    assert status_and_code(outsider.get(f"/trabajadores/{zoila}")) == (404, "TRABAJADOR_NO_EXISTE")


# ----------------------------------------------------------------------
# Perfil y catálogo
# ----------------------------------------------------------------------
def test_perfil_renombrar_y_comandos(run: Run, negocio: Negocio, app: AppClient):
    renamed = app.ok("PATCH", "/administrador", json={"nombre": "Admin  Renombrado"})
    assert renamed["administrador"]["nombre"] == "Admin Renombrado"
    renamed = app.ok("PATCH", "/negocio", json={"nombre": f"Negocio App {run.stamp}"})
    assert renamed["negocio"]["nombre"] == f"Negocio App {run.stamp}"
    assert status_and_code(app.request("PATCH", "/negocio", json={"nombre": "x"})) == (422, "NOMBRE_INVALIDO")

    # Las planillas nuevas usan los nombres nuevos.
    sheet = app.create("14-03-2025")["planilla"]["id"]
    cells = run.google.cells(sheet, "A2", "B6", "B7")
    assert cells == {"A2": f"Negocio App {run.stamp}", "B6": "Admin Renombrado", "B7": "14-03-2025"}

    commands = app.ok("GET", "/comandos")
    assert [c["id"] for c in commands][:4] == ["gasto", "efectivo", "saldo", "trabajador"]
    assert next(c for c in commands if c["id"] == "trabajador")["etiqueta"] == "Préstamo"
