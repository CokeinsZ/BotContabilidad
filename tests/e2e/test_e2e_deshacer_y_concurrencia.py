"""E2E: deshacer por mensaje completo y varios administradores a la vez."""
import threading

from e2e_support import BotUser, Run

INITIAL_COUNTERS = {"C135": 11, "C136": 11, "C137": 26, "C138": 39, "C139": 29, "C140": 11, "C141": 20}


def test_deshacer_revierte_un_mensaje_con_todos_los_tipos_de_comando(run: Run, admin: BotUser):
    google = run.google
    admin.send("hoja 01-06-2026")
    admin.send("saldo 50000")                    # mensaje anterior (no debe deshacerse)
    sheet = run.planilla("01-06-2026")

    replies = admin.send(
        "gasto 1000 pan, limpieza 2000, alimentacion 3000, administrador 4000, "
        "retiro 5000 banco, inversion 6000 horno, efectivo 70000 y saldo 80000")
    assert len(replies) == 8 and not any("⚠️" in r for r in replies)
    assert google.cells(sheet, "B11", "E11", "E20", "E26", "E39", "D29", "B39", "B42") == {
        "B11": 1000, "E11": 2000, "E20": 3000, "E26": 4000, "E39": 5000, "D29": 6000,
        "B39": 70000, "B42": 80000}

    assert admin.send("deshacer") == [
        "✅ Se deshizo: gasto 1000 pan, limpieza 2000, alimentacion 3000, administrador 4000, "
        "retiro 5000 banco, inversion 6000 horno, efectivo 70000, saldo 80000."]
    assert google.cells(sheet, *INITIAL_COUNTERS) == INITIAL_COUNTERS
    assert google.cells(sheet, "B11", "E11", "E20", "E26", "E39", "C39", "D29", "C29") == {
        c: "" for c in ("B11", "E11", "E20", "E26", "E39", "C39", "D29", "C29")}
    # Las celdas fijas vuelven a su valor anterior (no al de la plantilla).
    assert google.cells(sheet, "B39", "B42") == {"B39": 0, "B42": 50000}

    # Un solo nivel: el mensaje anterior ("saldo 50000") ya no se deshace.
    assert admin.send("deshacer") == ["⚠️ No hay un comando para deshacer."]


def test_deshacer_dentro_del_mismo_mensaje(run: Run, admin: BotUser):
    admin.send("hoja 02-06-2026")
    replies = admin.send("gasto 1000 arroz, deshacer y gasto 2000 sal")
    assert replies == ["Gasto registrado: $1.000 - arroz", "✅ Se deshizo: gasto 1000 arroz.",
                       "Gasto registrado: $2.000 - sal"]
    sheet = run.planilla("02-06-2026")
    assert run.google.values(sheet, "A11:B12")[0] == [["sal", 2000]]


def test_mensaje_fallido_no_reemplaza_el_deshacer(run: Run, admin: BotUser):
    admin.send("hoja 03-06-2026")
    admin.send("gasto 1000 pan")
    assert admin.send("hoja 31-02-2026")[0].startswith("⚠️ Formato de fecha inválido")
    assert admin.send("deshacer") == ["✅ Se deshizo: gasto 1000 pan."]


def test_deshacer_de_un_admin_no_borra_lo_del_otro(run: Run, admin: BotUser, admin2: BotUser):
    admin.send("hoja 04-06-2026")
    admin2.send("hoja 04-06-2026")
    sheet = run.planilla("04-06-2026")
    admin.send("gasto 111 harina")
    admin2.send("gasto 222 azucar")

    assert admin.send("deshacer") == ["✅ Se deshizo: gasto 111 harina."]
    assert run.google.values(sheet, "B11:B12")[0] == [[222]]
    assert run.google.value(sheet, "C135") == 12

    # El otro admin encuentra su fila aunque haya subido una posición.
    assert admin2.send("deshacer") == ["✅ Se deshizo: gasto 222 azucar."]
    assert run.google.values(sheet, "B11:B12")[0] == []
    assert run.google.value(sheet, "C135") == 11


def test_deshacer_no_pisa_una_celda_que_cambio_otro_admin(run: Run, admin: BotUser, admin2: BotUser):
    admin.send("hoja 05-06-2026")
    admin2.send("hoja 05-06-2026")
    admin.send("efectivo 100000")
    admin2.send("efectivo 250000")
    reply = admin.send("deshacer")[0]
    assert reply.startswith("✅ Se deshizo: efectivo 100000.")
    assert "la celda B39 fue modificada después" in reply
    assert run.google.value(run.planilla("05-06-2026"), "B39") == 250000


def test_admins_escribiendo_al_mismo_tiempo(run: Run):
    """4 administradores llenan a la vez la sección de gastos (24 filas)."""
    admins = [run.new_admin(f"Admin concurrente {n}") for n in range(4)]
    for user in admins:
        user.send("hoja 06-06-2026")
    errors = []

    def write(user: BotUser, base: int):
        try:
            for i in range(0, 6, 2):
                replies = user.send(f"gasto {base + i} item y gasto {base + i + 1} item")
                assert len(replies) == 2 and all(r.startswith("Gasto registrado") for r in replies), replies
        except Exception as error:   # noqa: BLE001 - se reporta abajo
            errors.append(error)

    # 4 admins x 3 mensajes x 2 gastos = 24 gastos simultáneos (la capacidad exacta).
    bases = (100, 200, 300, 400)
    threads = [threading.Thread(target=write, args=(user, base)) for user, base in zip(admins, bases)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors, errors

    sheet = run.planilla("06-06-2026")
    amounts = run.google.column(sheet, "B11:B34")
    assert sorted(amounts) == sorted(base + i for base in bases for i in range(6))   # ninguna fila pisada
    assert run.google.value(sheet, "C135") == 35
    assert "está llena" in admins[0].send("gasto 999 extra")[0]
