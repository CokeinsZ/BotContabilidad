"""E2E: planillas diarias, planillas adicionales y arrastre del saldo."""
from e2e_support import BotUser, Run


def balance_cells(run: Run, name: str, folder: str | None = None) -> dict:
    return run.google.cells(run.planilla(name, folder), "B39", "B42", "E60", "B58")


def test_saldo_se_arrastra_entre_planillas_del_dia_y_al_dia_siguiente(run: Run, admin: BotUser):
    google = run.google

    replies = admin.send("hoja 10-04-2026")
    assert "No existe una planilla para el día anterior: '09-04-2026'" in replies[0]
    admin.send("efectivo 100000, saldo 50000, gasto 20000 harina y retiro 30000 banco")
    assert balance_cells(run, "10-04-2026") == {"B39": 100000, "B42": 50000, "E60": 30000, "B58": 120000}

    # Segunda planilla: B42 = B58 de la primera.
    assert admin.send("segunda planilla") == [
        "Planilla '10-04-2026-2' seleccionada. Saldo de caja cargado desde '10-04-2026'."]
    admin.send("efectivo 40000 y retiro 10000 banco")
    assert balance_cells(run, "10-04-2026-2") == {"B39": 40000, "B42": 120000, "E60": 10000, "B58": 150000}

    # Tercera: saldo negativo (retiro mayor a lo que hay).
    assert "cargado desde '10-04-2026-2'" in admin.send("tercera planilla")[0]
    admin.send("retiro 200000 proveedor")
    assert balance_cells(run, "10-04-2026-3") == {"B39": 0, "B42": 150000, "E60": 200000, "B58": -50000}

    # Cuarta: arrastra el saldo negativo.
    assert "cargado desde '10-04-2026-3'" in admin.send("cuarta planilla")[0]
    admin.send("efectivo 80000")
    assert balance_cells(run, "10-04-2026-4") == {"B39": 80000, "B42": -50000, "E60": 0, "B58": 30000}

    # El día siguiente toma el saldo de la planilla MÁS ALTA del día anterior.
    assert admin.send("hoja 11-04-2026") == ["Planilla '11-04-2026' seleccionada."]
    next_day = run.planilla("11-04-2026")
    assert google.value(next_day, "B42") == 30000

    # Todos los saldos quedaron como NÚMERO (no como texto "$30,000").
    for name in ("10-04-2026-2", "10-04-2026-3", "10-04-2026-4", "11-04-2026"):
        assert google.entered_type(run.planilla(name), "B42") == "numberValue", name
    names = [n for n in google.planillas_of(run.planillas, "abril-2026") if n.startswith(("10-04", "11-04"))]
    assert names == ["10-04-2026", "10-04-2026-2", "10-04-2026-3", "10-04-2026-4", "11-04-2026"]

    # Encabezado de cada planilla nueva.
    header = google.cells(next_day, "A2", "B6", "B7")
    assert header == {"A2": run.business_name, "B6": admin.name, "B7": "11-04-2026"}


def test_planillas_adicionales_casos_limite(run: Run, admin: BotUser):
    google = run.google

    # Sin la planilla base del día no se puede crear la segunda.
    assert admin.send("segunda planilla 15-04-2026") == [
        "⚠️ No existe la planilla '15-04-2026'. Las planillas adicionales se crean en orden."]
    assert google.planillas_of(run.planillas, "abril-2026").count("15-04-2026-2") == 0

    admin.send("hoja 15-04-2026")
    admin.send("efectivo 1000")
    admin.send("segunda planilla")

    # No se puede saltar el orden.
    assert admin.send("cuarta planilla") == [
        "⚠️ No existe la planilla '15-04-2026-3'. Las planillas adicionales se crean en orden."]

    # Volver a pedir una que ya existe solo la selecciona (no duplica).
    assert admin.send("2 planilla") == ["Planilla '15-04-2026-2' seleccionada."]
    assert admin.send("segunda planilla") == ["Planilla '15-04-2026-2' seleccionada."]

    # Con fecha explícita, aunque la planilla activa sea de otro día.
    admin.send("hoja 16-04-2026")
    admin.send("hoja 15-04-2026")
    assert admin.send("segunda planilla 16-04-2026") == [
        "Planilla '16-04-2026-2' seleccionada. Saldo de caja cargado desde '16-04-2026'."]

    # Crear/seleccionar planillas no se deshace: 'deshacer' revierte el último
    # movimiento (el efectivo de la 15-04), y las planillas siguen ahí.
    assert admin.send("deshacer") == ["✅ Se deshizo: efectivo 1000."]
    assert google.value(run.planilla("15-04-2026"), "B39") == 0

    assert google.planillas_of(run.planillas, "abril-2026").count("15-04-2026-2") == 1
    names = [n for n in google.planillas_of(run.planillas, "abril-2026") if n.startswith(("15-04", "16-04"))]
    assert names == ["15-04-2026", "15-04-2026-2", "16-04-2026", "16-04-2026-2"]


def test_fecha_invalida(run: Run, admin: BotUser):
    replies = admin.send("hoja 31-02-2026")
    assert replies == ["⚠️ Formato de fecha inválido: '31-02-2026'. Usa dd-mm-aaaa."]
    assert run.google.planillas_of(run.planillas, "febrero-2026") == []


def test_saldo_cruza_cambio_de_mes_y_de_anio(run: Run, admin: BotUser):
    admin.send("hoja 31-12-2026")
    admin.send("efectivo 70000 y retiro 5000 caja menor")
    assert admin.send("hoja 01-01-2027") == ["Planilla '01-01-2027' seleccionada."]
    assert run.google.value(run.planilla("01-01-2027"), "B42") == 65000
    assert run.google.planillas_of(run.planillas, "diciembre-2026") == ["31-12-2026"]
    assert run.google.planillas_of(run.planillas, "enero-2027") == ["01-01-2027"]


def test_saldo_total_no_numerico_del_dia_anterior(run: Run, admin: BotUser):
    admin.send("hoja 20-04-2026")
    previous = run.planilla("20-04-2026")
    run.google.set_value(previous, "B39", "abc")     # rompe B58 (=B39+B42-E60 -> #VALUE!)

    replies = admin.send("hoja 21-04-2026")
    assert "El saldo total de la planilla anterior no es un número" in replies[0]
    assert replies[0].endswith("Planilla '21-04-2026' seleccionada.")
    assert run.google.value(run.planilla("21-04-2026"), "B42") == 0


def test_saldo_se_copia_al_crear_y_luego_se_corrige_con_saldo(run: Run, admin: BotUser):
    """Comportamiento documentado: el saldo se copia al CREAR la planilla."""
    google = run.google
    admin.send("hoja 22-04-2026")
    admin.send("efectivo 1000")
    admin.send("hoja 23-04-2026")
    day_23 = run.planilla("23-04-2026")
    assert google.value(day_23, "B42") == 1000

    # Si después se corrige el día anterior, la planilla ya creada no cambia...
    admin.send("hoja 22-04-2026")
    admin.send("efectivo 5000")
    assert google.value(run.planilla("22-04-2026"), "B58") == 5000
    assert google.value(day_23, "B42") == 1000

    # ...y se ajusta a mano con 'saldo' (deshacible: vuelve al valor arrastrado).
    admin.send("hoja 23-04-2026")
    assert admin.send("saldo 5000") == ["Saldo registrado: $5.000"]
    assert google.value(day_23, "B42") == 5000
    admin.send("deshacer")
    assert google.value(day_23, "B42") == 1000


def test_resumen_coincide_con_la_planilla(run: Run, admin: BotUser):
    admin.send("hoja 01-07-2026")
    admin.send("efectivo 200000, saldo 50000, gasto 30000 pan, limpieza 2500 y retiro 20000 banco")
    summary = admin.send("terminar_dia")[0]
    sheet = run.planilla("01-07-2026")
    totals = run.google.cells(sheet, "B38", "B39", "B40", "B42", "B58")
    assert totals == {"B38": 32500, "B39": 200000, "B40": 232500, "B42": 50000, "B58": 230000}
    assert f"/spreadsheets/d/{sheet}/" in summary
    for line in ("Gastos totales del día: $32.500", "Efectivo del día: $200.000",
                 "Ventas totales del día: $232.500", "Saldo previo: $50.000",
                 "Saldo total: $230.000"):
        assert line in summary


def test_corregir_saldos_encadena_todas_las_planillas_siguientes(run: Run):
    """Negocio propio: corregir_saldos recorre TODAS las planillas del negocio."""
    business_id, folder = run.new_business("corregir-saldos")
    admin = run.new_admin("Admin saldos", business_id=business_id)
    google = run.google

    def b42(name):
        return google.value(run.planilla(name, folder), "B42")

    admin.send("hoja 28-04-2026")
    admin.send("efectivo 1000")
    admin.send("hoja 29-04-2026")
    admin.send("efectivo 500")                       # B42 = 1000 -> B58 = 1500
    admin.send("segunda planilla")
    admin.send("retiro 200 banco")                   # B42 = 1500 -> B58 = 1300
    admin.send("hoja 01-05-2026")                    # falta el 30-04 (y cambia de mes): B42 = 0
    assert [b42(n) for n in ("29-04-2026", "29-04-2026-2", "01-05-2026")] == [1000, 1500, 0]

    # Se corrige el día 28 y se re-encadenan los saldos desde ahí.
    admin.send("hoja 28-04-2026")
    admin.send("efectivo 4000")
    assert admin.send("corregir_saldos") == [
        "🔄 Saldos corregidos desde '28-04-2026':\n"
        "• 29-04-2026: $1.000 → $4.000\n"
        "• 29-04-2026-2: $1.500 → $4.500\n"
        "• 01-05-2026: $0 → $4.300"]
    assert [b42(n) for n in ("29-04-2026", "29-04-2026-2", "01-05-2026")] == [4000, 4500, 4300]
    assert b42("28-04-2026") == 0                    # la seleccionada no se toca
    for name in ("29-04-2026", "29-04-2026-2", "01-05-2026"):
        assert google.entered_type(run.planilla(name, folder), "B42") == "numberValue"

    # Deshacer lo revierte todo.
    assert admin.send("deshacer") == ["✅ Se deshizo: corregir_saldos."]
    assert [b42(n) for n in ("29-04-2026", "29-04-2026-2", "01-05-2026")] == [1000, 1500, 0]

    # En lenguaje natural, desde una planilla adicional (solo cambia lo posterior).
    replies = admin.send("arregla los saldos desde la segunda planilla del 29-04-2026")
    assert replies[0] == "Planilla '29-04-2026-2' seleccionada."
    assert replies[1] == "🔄 Saldos corregidos desde '29-04-2026-2':\n• 01-05-2026: $0 → $1.300"
    assert [b42(n) for n in ("29-04-2026", "29-04-2026-2", "01-05-2026")] == [1000, 1500, 1300]

    # Si ya están bien, lo dice; desde la última, no hay nada que corregir.
    admin.send("hoja 29-04-2026")
    assert admin.send("corrige los saldos") == [
        "✅ Los saldos de las 2 planilla(s) posteriores a '29-04-2026' ya estaban bien."]
    admin.send("hoja 01-05-2026")
    assert admin.send("corregir_saldos") == [
        "No hay planillas posteriores a '01-05-2026': no hay saldos que corregir."]
