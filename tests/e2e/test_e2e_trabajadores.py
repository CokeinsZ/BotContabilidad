"""E2E: préstamos a trabajadores, nombres similares y nómina.

Cada prueba usa nombres de trabajador propios (la carpeta de trabajadores es
compartida por toda la corrida y la búsqueda es por "contiene").
"""
from e2e_support import BotUser, Run, menu_options, today_str

TEMPLATE_ID_ENV = "WORKERS_TEMPLATE_ID"


def loans(run: Run, worker: str, rows: int = 3) -> list:
    """Montos de los primeros `rows` vales del archivo del trabajador."""
    return run.google.column(run.worker(worker), f"principal!B13:B{12 + rows}")


def counter(run: Run, worker: str) -> int:
    return run.google.value(run.worker(worker), "principal!C123")


def daily_loans(run: Run, sheet: str, first: int, last: int, folder: str | None = None) -> list:
    rows = run.google.values(run.planilla(sheet, folder), f"C{first}:D{last}")[0]
    return [tuple(r) for r in rows]


def created(worker: str) -> str:
    return f"👤 Se creó el archivo del trabajador '{worker}'."


def saved(worker: str) -> str:
    return f"📄 Préstamo guardado en el archivo de '{worker}'."


# ----------------------------------------------------------------------
# Préstamos y nombres similares
# ----------------------------------------------------------------------
def test_mismo_nombre_con_distinto_apellido_o_descripcion(run: Run, admin: BotUser):
    admin.send("hoja 02-05-2026")

    # Mismo nombre, distinta descripción: son trabajadores distintos.
    assert admin.send("trabajador 10000 jose salon") == [
        "Préstamo registrado: $10.000 - jose salon", created("jose salon"), saved("jose salon")]
    assert admin.send("trabajador 20000 jose panadero") == [
        "Préstamo registrado: $20.000 - jose panadero", created("jose panadero"), saved("jose panadero")]

    # Nombre completo (con mayúsculas y tildes): va directo a su archivo.
    assert admin.send("trabajador 5000 JOSÉ SALÓN") == [
        "Préstamo registrado: $5.000 - jose salon", saved("jose salon")]

    # Solo "jose": es ambiguo -> menú con los dos + crear nuevo.
    replies = admin.send("trabajador 1000 jose")
    assert replies[0] == "Préstamo registrado: $1.000 - jose"
    options = menu_options(replies[1])
    assert set(options) == {"jose salon", "jose panadero", "__crear__"}
    assert options["__crear__"] == 3

    # Opción inválida: vuelve a preguntar.
    assert admin.send("7") == ["⚠️ Opción inválida: 7.", replies[1]]
    assert admin.send(str(options["jose panadero"])) == [saved("jose panadero")]

    # Crear un "jose" a secas desde el menú.
    options = menu_options(admin.send("trabajador 2000 jose")[1])
    assert admin.send(str(options["__crear__"])) == [created("jose"), saved("jose")]

    # Ya existe "jose": sigue preguntando (la búsqueda es por "contiene"),
    # ahora con 3 trabajadores + crear.
    options = menu_options(admin.send("trabajador 500 jose")[1])
    assert set(options) == {"jose", "jose salon", "jose panadero", "__crear__"}
    assert admin.send(str(options["jose"])) == [saved("jose")]

    # Nombre parecido que CONTIENE a otro: "josefina" no coincide con ningún
    # archivo existente (ninguno contiene "josefina") -> archivo nuevo.
    assert admin.send("trabajador 700 josefina") == [
        "Préstamo registrado: $700 - josefina", created("josefina"), saved("josefina")]
    # Pero "jose" ahora también lista a "josefina".
    options = menu_options(admin.send("trabajador 100 jose")[1])
    assert set(options) == {"jose", "jose salon", "jose panadero", "josefina", "__crear__"}

    # Si en vez del número llega otro mensaje, el préstamo se cancela completo
    # (se borra de la planilla) y se avisa.
    assert admin.send("gasto 100 pan") == [
        "⚠️ No escogiste ninguna opción del menú, así que se canceló 'trabajador 100 jose' "
        "y se borró de la planilla.",
        "Gasto registrado: $100 - pan"]

    files = run.worker_files()   # además verifica que no haya duplicados
    assert {"jose", "jose salon", "jose panadero", "josefina"} <= set(files)
    assert loans(run, "jose salon") == [10000, 5000, 0]
    assert loans(run, "jose panadero") == [20000, 1000, 0]
    assert loans(run, "jose") == [2000, 500, 0]
    assert loans(run, "josefina") == [700, 0, 0]
    assert [counter(run, w) for w in ("jose salon", "jose panadero", "jose", "josefina")] == [15, 15, 15, 14]
    assert daily_loans(run, "02-05-2026", 11, 19) == [
        ("jose salon", 10000), ("jose panadero", 20000), ("jose salon", 5000), ("jose", 1000),
        ("jose", 2000), ("jose", 500), ("josefina", 700)]


def test_dos_prestamos_ambiguos_en_un_mismo_mensaje(run: Run, admin: BotUser):
    admin.send("hoja 03-05-2026")
    replies = admin.send(
        "trabajador 1000 luis norte, trabajador 1000 luis sur, "
        "trabajador 1000 rosa alta y trabajador 1000 rosa baja")
    assert replies.count(created("luis sur")) == 1 and replies.count(created("rosa baja")) == 1

    replies = admin.send("trabajador 2000 luis y trabajador 3000 rosa")
    assert replies[0] == "Préstamo registrado: $2.000 - luis"
    luis_options = menu_options(replies[1])
    assert set(luis_options) == {"luis norte", "luis sur", "__crear__"}
    assert replies[2] == "Préstamo registrado: $3.000 - rosa"
    assert replies[3].startswith("⏳ También hay varios trabajadores con nombre similar a 'rosa'")

    # Se responde un menú a la vez: al responder el primero llega el segundo.
    replies = admin.send(str(luis_options["luis sur"]))
    assert replies[0] == saved("luis sur")
    rosa_options = menu_options(replies[1])
    assert set(rosa_options) == {"rosa alta", "rosa baja", "__crear__"}
    assert admin.send(str(rosa_options["rosa baja"])) == [saved("rosa baja")]

    assert loans(run, "luis sur", 2) == [1000, 2000]
    assert loans(run, "rosa baja", 2) == [1000, 3000]

    # Deshacer revierte el mensaje completo: filas de la planilla Y vales.
    assert admin.send("deshacer") == ["✅ Se deshizo: trabajador 2000 luis, trabajador 3000 rosa."]
    assert loans(run, "luis sur", 2) == [1000, 0]
    assert loans(run, "rosa baja", 2) == [1000, 0]
    assert counter(run, "luis sur") == 14 and counter(run, "rosa baja") == 14
    assert loans(run, "luis norte", 2) == [1000, 0]
    assert len(daily_loans(run, "03-05-2026", 11, 26)) == 4


def test_mayusculas_tildes_y_enie(run: Run, admin: BotUser):
    import os
    admin.send("hoja 04-05-2026")
    # Archivo creado A MANO, con mayúsculas y tildes.
    run.google.copy(os.environ[TEMPLATE_ID_ENV], "Andrés Gómez", run.trabajadores)
    assert admin.send("trabajador 1000 andres gomez") == [
        "Préstamo registrado: $1.000 - andres gomez", saved("Andrés Gómez")]

    replies = admin.send("trabajador 1000 Muñoz")
    enie_file = next(n for n in run.worker_files() if n in ("muñoz", "munoz"))
    assert replies[1] == created(enie_file)
    assert admin.send("trabajador 2000 MUNOZ")[-1] == saved(enie_file)

    files = run.worker_files()
    assert "andres gomez" not in files and "Andrés Gómez" in files
    assert loans(run, "Andrés Gómez", 2) == [1000, 0]
    assert loans(run, enie_file, 2) == [1000, 2000]


# ----------------------------------------------------------------------
# Nómina
# ----------------------------------------------------------------------
def test_prestamos_nomina_y_deshacer_de_la_nomina(run: Run, admin: BotUser):
    google = run.google
    admin.send("hoja 05-05-2026")
    replies = admin.send(
        "trabajador 10000 carlos ruiz, trabajador 15000 carlos ruiz y trabajador 5000 carlos ruiz")
    assert replies.count(created("carlos ruiz")) == 1     # no se duplica dentro del lote
    file_id = run.worker("carlos ruiz")
    assert google.values(file_id, "principal!A13:B15")[0] == [
        ["05-05-2026", 10000], ["05-05-2026", 15000], ["05-05-2026", 5000]]
    assert google.cells(file_id, "principal!B30", "principal!C123", "principal!A2") == {
        "principal!B30": 30000, "principal!C123": 16, "principal!A2": run.business_name}

    today = today_str()
    replies = admin.send("nomina 300000 carlos ruiz")
    assert replies[0] == "Pago de nómina registrado en planilla: $300.000 - carlos ruiz"
    assert replies[1].startswith("📋 Nómina de carlos ruiz\nSuma de préstamos: $30.000\n")
    assert replies[2] == f"✅ Nómina procesada: hoja '{today}' creada y hoja principal limpiada."

    assert sorted(google.sheet_titles(file_id)) == sorted(["principal", today])
    archived = google.values(file_id, f"'{today}'!A4:B6")[0]
    assert archived == [["05-05-2026", 10000], ["05-05-2026", 15000], ["05-05-2026", 5000]]
    assert google.column(file_id, "principal!A13:A28") == [""] * 16
    assert google.column(file_id, "principal!B13:B28") == [0] * 16
    assert google.cells(file_id, "principal!B30", "principal!C123") == {
        "principal!B30": 0, "principal!C123": 13}
    assert daily_loans(run, "05-05-2026", 14, 14) == [("carlos ruiz", 300000)]

    # Deshacer la nómina: se borra la hoja archivada y vuelven los vales.
    assert admin.send("deshacer") == ["✅ Se deshizo: nomina 300000 carlos ruiz."]
    assert google.sheet_titles(file_id) == ["principal"]
    assert loans(run, "carlos ruiz") == [10000, 15000, 5000]
    assert counter(run, "carlos ruiz") == 16
    assert daily_loans(run, "05-05-2026", 14, 14) == []

    # Dos cierres el mismo día (el segundo vía retiro): nombres únicos.
    admin.send("nomina 300000 carlos ruiz")
    replies = admin.send("retiro 50000 nomina de carlos ruiz")
    assert replies[0].startswith("Retiro registrado: $50.000 - nomina")
    assert "Suma de préstamos: $0" in replies[1]
    assert replies[2] == f"✅ Nómina procesada: hoja '{today} (2)' creada y hoja principal limpiada."
    assert sorted(google.sheet_titles(file_id)) == sorted(["principal", today, f"{today} (2)"])

    # Después de la nómina, los vales vuelven a empezar en la fila 13.
    admin.send("trabajador 2500 carlos ruiz")
    assert loans(run, "carlos ruiz", 2) == [2500, 0]
    assert counter(run, "carlos ruiz") == 14


def test_nomina_casos_limite(run: Run, admin: BotUser, admin2: BotUser):
    google = run.google
    admin.send("hoja 06-05-2026")

    # Trabajador sin archivo: el pago queda en la planilla, con aviso.
    assert admin.send("nomina 1000 fantasma gris") == [
        "Pago de nómina registrado en planilla: $1.000 - fantasma gris",
        "⚠️ No se encontró archivo para el trabajador 'fantasma gris'."]

    # "retiro ... nomina" sin nombre: retiro normal, no cierra nada.
    assert admin.send("retiro 5000 nomina") == ["Retiro registrado: $5.000 - nomina"]

    # Nómina ambigua: menú SIN opción de crear.
    admin.send("trabajador 1000 pablo uno y trabajador 2000 pablo dos")
    replies = admin.send("nomina 1000 pablo")
    options = menu_options(replies[1])
    assert set(options) == {"pablo uno", "pablo dos"}
    assert admin.send("3")[0] == "⚠️ Opción inválida: 3."
    replies = admin.send(str(options["pablo dos"]))
    assert replies[0].startswith("📋 Nómina de pablo dos\nSuma de préstamos: $2.000")
    assert counter(run, "pablo dos") == 13
    assert counter(run, "pablo uno") == 14                       # el otro no se toca
    assert google.sheet_titles(run.worker("pablo uno")) == ["principal"]

    # Deshacer una nómina cuando OTRO admin ya registró un vale nuevo:
    # no se restaura (se perdería el vale) y se avisa.
    admin.send("nomina 1000 pablo uno")
    admin2.send("hoja 06-05-2026")
    admin2.send("trabajador 700 pablo uno")
    reply = admin.send("deshacer")[0]
    assert "recibió vales nuevos después de la nómina" in reply
    assert loans(run, "pablo uno", 2) == [700, 0]
    assert len(google.sheet_titles(run.worker("pablo uno"))) == 2   # la hoja archivada sigue


def test_limite_de_vales_del_trabajador(run: Run, admin: BotUser):
    google = run.google
    admin.send("hoja 10-05-2026")
    amounts = list(range(1001, 1017))
    for start in (0, 8):
        chunk = amounts[start:start + 8]
        replies = admin.send(", ".join(f"trabajador {a} vale lleno" for a in chunk))
        assert not any("⚠️" in r for r in replies), replies

    sheet = run.planilla("10-05-2026")
    file_id = run.worker("vale lleno")
    assert google.column(sheet, "D11:D26") == amounts             # sección diaria llena
    assert google.column(file_id, "principal!B13:B28") == amounts  # 16 vales llenos
    assert google.cells(sheet, "C136") == {"C136": 27}
    assert google.cells(file_id, "principal!C123", "principal!B30") == {
        "principal!C123": 29, "principal!B30": sum(amounts)}

    # 17º préstamo: la sección de la planilla está llena -> no se toca el archivo.
    assert admin.send("trabajador 9999 vale lleno") == [
        "⚠️ La sección 'préstamos a trabajadores' de la planilla está llena (16 filas). "
        "Crea una planilla adicional del día con 'segunda planilla' para seguir registrando."]
    assert google.value(file_id, "principal!C123") == 29

    # En una planilla adicional sí cabe, pero el archivo del trabajador está lleno.
    admin.send("segunda planilla")
    assert admin.send("trabajador 9999 vale lleno") == [
        "Préstamo registrado: $9.999 - vale lleno",
        "⚠️ El archivo de 'vale lleno' ya tiene sus 16 vales ocupados: haz la nómina para "
        "cerrar el período. El préstamo quedó registrado solo en la planilla."]
    assert google.cells(file_id, "principal!B29", "principal!B30", "principal!A30", render="FORMULA") == {
        "principal!B29": "", "principal!B30": "=SUM(B13:B29)", "principal!A30": "TOTAL"}

    # La nómina libera el archivo.
    admin.send("nomina 1 vale lleno")
    admin.send("trabajador 500 vale lleno")
    assert loans(run, "vale lleno", 2) == [500, 0]


def test_archivos_de_trabajador_inesperados(run: Run, admin: BotUser):
    import os
    admin.send("hoja 11-05-2026")

    # Hoja de cálculo vacía (no viene de la plantilla): no hay contador.
    run.google.create_spreadsheet("lucia vacia", run.trabajadores)
    assert admin.send("trabajador 1000 lucia vacia") == [
        "Préstamo registrado: $1.000 - lucia vacia",
        "⚠️ No se pudo registrar el préstamo en el archivo de 'lucia vacia'."]

    # Plantilla con la hoja "principal" renombrada.
    file_id = run.google.copy(os.environ[TEMPLATE_ID_ENV], "marta renombrada", run.trabajadores)
    run.google.rename_sheet(file_id, "principal", "Hoja 1")
    replies = admin.send("nomina 1000 marta renombrada")
    assert replies[-1] == "⚠️ El archivo de 'marta renombrada' no tiene la hoja 'principal'."
    assert run.google.sheet_titles(file_id) == ["Hoja 1"]


def test_negocio_sin_carpeta_de_trabajadores(run: Run):
    admin = run.new_admin("Admin sin trabajadores", business_id=run.no_workers_business_id)
    admin.send("hoja 12-05-2026")
    assert admin.send("trabajador 1000 pedro") == [
        "Préstamo registrado: $1.000 - pedro",
        "⚠️ Este negocio no tiene configurada la carpeta de trabajadores (workers_folder_id), "
        "así que el préstamo no se registró en el archivo individual."]
    assert admin.send("nomina 2000 pedro") == [
        "Pago de nómina registrado en planilla: $2.000 - pedro",
        "⚠️ Este negocio no tiene configurada la carpeta de trabajadores (workers_folder_id)."]
    assert daily_loans(run, "12-05-2026", 11, 12, folder=run.no_workers_planillas) == [
        ("pedro", 1000), ("pedro", 2000)]


def cancelled(command: str) -> str:
    return (f"⚠️ No escogiste ninguna opción del menú, así que se canceló '{command}' "
            "y se borró de la planilla.")


def test_menu_sin_responder_cancela_el_comando_completo(run: Run, admin: BotUser):
    google = run.google
    admin.send("hoja 07-05-2026")
    admin.send("trabajador 1000 tomas norte y trabajador 1000 tomas sur")
    sheet = run.planilla("07-05-2026")

    # Préstamo: llega otro mensaje en vez del número.
    assert menu_options(admin.send("trabajador 2000 tomas")[1])
    assert admin.send("gasto 300 sal") == [cancelled("trabajador 2000 tomas"), "Gasto registrado: $300 - sal"]
    assert daily_loans(run, "07-05-2026", 11, 13) == [("tomas norte", 1000), ("tomas sur", 1000)]
    assert loans(run, "tomas norte", 2) == [1000, 0] and loans(run, "tomas sur", 2) == [1000, 0]

    # Nómina: llega un mensaje sin comandos.
    assert menu_options(admin.send("nomina 5000 tomas")[1])
    assert admin.send("jajaja ok") == [
        cancelled("nomina 5000 tomas"),
        "🤔 No encontré ningún comando en tu mensaje. Escribe 'instrucciones' para ver lo que puedo hacer."]
    assert daily_loans(run, "07-05-2026", 11, 13) == [("tomas norte", 1000), ("tomas sur", 1000)]
    assert counter(run, "tomas norte") == 14 and counter(run, "tomas sur") == 14   # nada se cerró

    # Retiro para nómina: llega 'deshacer'. El retiro se cancela y ya no
    # queda nada más de ese mensaje por deshacer.
    replies = admin.send("retiro 7000 nomina tomas")
    assert replies[0].startswith("Retiro registrado: $7.000")
    command = replies[0].split(": ", 1)[1].replace("$7.000 - ", "retiro 7000 ")
    assert admin.send("deshacer") == [cancelled(command), "⚠️ No hay un comando para deshacer."]
    assert google.values(sheet, "C39:E39")[0] == []
    assert google.value(sheet, "C138") == 39
