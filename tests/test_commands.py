"""Pruebas del núcleo de comandos con Google Sheets/Drive falsos en memoria."""
import threading

from fakes import col_values

COUNTERS = {"gastos": "C135", "trabajadores": "C136", "retiros": "C138", "aseo": "C140"}


def counter(bot, name, phone="999"):
    return bot.active_file(phone).raw(COUNTERS[name])


# ----------------------------------------------------------------------
# Planillas y saldo
# ----------------------------------------------------------------------
def test_new_sheet_propagates_previous_total_as_number(bot):
    bot.send("hoja 23-11-2026", "efectivo 350.000", "saldo 1.000.000", "gasto 50000 harina")
    previous = bot.active_file()
    assert previous.evaluate(previous.sheets["Hoja 1"]["cells"], "=B39+B42-E60") == 1_350_000

    bot.send("hoja 24-11-2026")
    b42 = bot.active_file().raw("B42")
    assert b42 == 1_350_000 and isinstance(b42, int)   # número, no "$1.350.000"


def test_additional_sheet_takes_balance_from_previous_of_same_day(bot):
    bot.send("hoja 24-11-2026", "efectivo 100000")
    responses = bot.send("segunda planilla")
    assert "Saldo de caja cargado desde '24-11-2026'" in responses[0]
    assert bot.session().active_sheet_name == "24-11-2026-2"
    assert bot.active_file().raw("B42") == 100000


def test_non_numeric_previous_total_warns_and_writes_zero(bot):
    bot.send("hoja 23-11-2026")
    bot.active_file().sheets["Hoja 1"]["cells"][(2, 58)] = "#VALUE!"
    responses = bot.send("hoja 24-11-2026")
    assert "no es un número" in responses[0]
    assert bot.active_file().raw("B42") == 0


def test_summary_reads_named_cells_including_b58(bot):
    bot.send("hoja 24-11-2026", "efectivo 200000", "saldo 50000", "gasto 30000 pan",
             "retiro 20000 banco")
    summary = bot.send("terminar_dia")[0]
    assert "Gastos totales del día: $30.000" in summary
    assert "Efectivo del día: $200.000" in summary
    assert "Ventas totales del día: $230.000" in summary
    assert "Saldo previo: $50.000" in summary
    assert "Saldo total: $230.000" in summary   # B39 + B42 - E60 = 200000 + 50000 - 20000


# ----------------------------------------------------------------------
# Lotes y deshacer
# ----------------------------------------------------------------------
def test_batch_registers_every_command_separately(bot):
    bot.send("hoja 24-11-2026")
    responses = bot.send("gasto 5.000 pan", "gasto 3000 leche", "limpieza 2000")
    assert responses == [
        "Gasto registrado: $5.000 - pan",
        "Gasto registrado: $3.000 - leche",
        "Gasto de limpieza registrado: $2.000",
    ]
    assert col_values(bot.service, bot.session().active_sheet_id, "A11:B12") == [
        ["pan", 5000], ["leche", 3000]]


def test_undo_reverts_the_whole_last_message(bot):
    bot.send("hoja 24-11-2026", "gasto 1000 previo")
    bot.send("gasto 5000 pan", "gasto 3000 leche", "limpieza 2000", "efectivo 90000")
    response = bot.send("deshacer")[0]
    assert response.startswith("✅ Se deshizo: gasto 5000 pan, gasto 3000 leche, limpieza 2000, efectivo 90000")

    sheet = bot.session().active_sheet_id
    assert col_values(bot.service, sheet, "A11:B13") == [["previo", 1000]]
    assert counter(bot, "gastos") == 12
    assert counter(bot, "aseo") == 11
    assert bot.active_file().raw("B39") == 0
    # El deshacer es de un nivel (como antes): solo el último mensaje.
    assert bot.send("deshacer") == ["⚠️ No hay un comando para deshacer."]


def test_undo_inside_the_same_message_reverts_previous_commands_of_that_message(bot):
    bot.send("hoja 24-11-2026", "gasto 1000 previo")
    responses = bot.send("gasto 5000 pan", "deshacer", "gasto 2000 sal")
    assert responses[1] == "✅ Se deshizo: gasto 5000 pan."
    sheet = bot.session().active_sheet_id
    assert col_values(bot.service, sheet, "A11:B13") == [["previo", 1000], ["sal", 2000]]
    bot.send("deshacer")   # solo "gasto 2000 sal"
    assert col_values(bot.service, sheet, "A11:B13") == [["previo", 1000]]


def test_undo_survives_sheet_change_in_same_message(bot):
    bot.send("hoja 23-11-2026")
    first = bot.session().active_sheet_id
    bot.send("gasto 1000 ayer", "hoja 24-11-2026", "gasto 2000 hoy")
    second = bot.session().active_sheet_id
    bot.send("deshacer")
    assert col_values(bot.service, first, "A11:B11") == []
    assert col_values(bot.service, second, "A11:B11") == []


# ----------------------------------------------------------------------
# Límites de regiones
# ----------------------------------------------------------------------
def test_region_full_is_rejected_without_overwriting_next_section(bot):
    bot.send("hoja 24-11-2026")
    responses = bot.send(*[f"limpieza {1000 + i}" for i in range(9)])
    assert all(r.startswith("Gasto de limpieza registrado") for r in responses[:8])
    assert "La sección 'aseo' de la planilla está llena (8 filas)" in responses[8]
    bot.send("alimentacion 7000")
    assert bot.active_file().raw("E20") == 7000   # la alimentación no fue pisada
    assert counter(bot, "aseo") == 19


# ----------------------------------------------------------------------
# Concurrencia entre administradores
# ----------------------------------------------------------------------
def test_concurrent_admins_never_share_a_row(bot):
    bot.send("hoja 24-11-2026")
    sheet_id = bot.session().active_sheet_id
    bot.session("998").set_active_sheet(sheet_id, "24-11-2026")
    bot.service.read_delay = 0.01   # agranda la ventana de carrera

    def worker(phone, start):
        for i in range(6):
            bot.send(f"gasto {start + i} item", phone=phone)

    threads = [threading.Thread(target=worker, args=(p, s)) for p, s in [("999", 100), ("998", 200)]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rows = col_values(bot.service, sheet_id, "A11:B34")
    assert len(rows) == 12
    assert sorted(r[1] for r in rows) == [*range(100, 106), *range(200, 206)]


def test_undo_removes_own_row_not_the_other_admins(bot):
    bot.send("hoja 24-11-2026")
    sheet_id = bot.session().active_sheet_id
    bot.session("998").set_active_sheet(sheet_id, "24-11-2026")
    bot.send("gasto 5000 de-999", phone="999")
    bot.send("gasto 7000 de-998", phone="998")
    bot.send("deshacer", phone="999")
    assert col_values(bot.service, sheet_id, "A11:B12") == [["de-998", 7000]]
    assert counter(bot, "gastos") == 12
    # Y el deshacer del otro admin encuentra su fila aunque se haya movido.
    bot.send("deshacer", phone="998")
    assert col_values(bot.service, sheet_id, "A11:B12") == []
    assert counter(bot, "gastos") == 11


def test_cell_undo_does_not_clobber_newer_value(bot):
    bot.send("hoja 24-11-2026")
    sheet_id = bot.session().active_sheet_id
    bot.session("998").set_active_sheet(sheet_id, "24-11-2026")
    bot.send("efectivo 100000", phone="999")
    bot.send("efectivo 250000", phone="998")
    response = bot.send("deshacer", phone="999")[0]
    assert "fue modificada después" in response
    assert bot.active_file().raw("B39") == 250000


# ----------------------------------------------------------------------
# Préstamos a trabajadores
# ----------------------------------------------------------------------
def test_loan_creates_worker_file_and_undo_reverts_both(bot):
    bot.send("hoja 24-11-2026")
    responses = bot.send("trabajador 20000 María José")
    assert responses == [
        "Préstamo registrado: $20.000 - maria jose",
        "👤 Se creó el archivo del trabajador 'maria jose'.",
        "📄 Préstamo guardado en el archivo de 'maria jose'.",
    ]
    file_id = bot.drive.workers[0][0]
    assert col_values(bot.service, file_id, "principal!A13:B13") == [["24-11-2026", 20000]]
    assert bot.service.files[file_id].raw("principal!A2") == "Pruebas"

    bot.send("deshacer")
    assert col_values(bot.service, file_id, "principal!A13:B13") == [["", 0]]
    assert bot.service.files[file_id].raw("principal!C123") == 13
    assert counter(bot, "trabajadores") == 11


def test_loan_matches_existing_file_ignoring_case_and_accents(bot):
    bot.send("hoja 24-11-2026")
    file_id = bot.drive.add_worker("María José Muñoz")   # creado a mano
    responses = bot.send("trabajador 10000 MARIA JOSE munoz")
    assert responses[-1] == "📄 Préstamo guardado en el archivo de 'María José Muñoz'."
    assert len(bot.drive.workers) == 1
    assert col_values(bot.service, file_id, "principal!B13") == [[10000]]


def test_loan_not_written_to_worker_file_when_daily_sheet_fails(bot):
    """Bug 2: antes se escribía en el archivo y el paso se colaba en el deshacer anterior."""
    bot.send("hoja 24-11-2026", "gasto 7000 harina")
    file_id = bot.drive.add_worker("pedro")
    bot.active_file().sheets["Hoja 1"]["cells"][(3, 136)] = 27   # región de préstamos llena

    responses = bot.send("trabajador 10000 pedro")
    assert responses == [
        "⚠️ La sección 'préstamos a trabajadores' de la planilla está llena (16 filas). "
        "Crea una planilla adicional del día con 'segunda planilla' para seguir registrando."
    ]
    assert col_values(bot.service, file_id, "principal!B13") == [[0]]
    snapshot = bot.session().undo_snapshot
    assert snapshot.description == "gasto 7000 harina"
    assert len(snapshot.steps) == 1


def test_loan_selection_menu_and_undo_of_both_parts(bot):
    bot.send("hoja 24-11-2026")
    maria = bot.drive.add_worker("maria")
    bot.drive.add_worker("mariana")
    responses = bot.send("trabajador 20000 maria", "gasto 3000 pan")
    assert "1. maria" in responses[1] and "3. ➕ Crear nuevo trabajador 'maria'" in responses[1]
    assert bot.send("1") == ["📄 Préstamo guardado en el archivo de 'maria'."]
    assert bot.drive.workers[0][1] == "maria"
    assert col_values(bot.service, maria, "principal!B13") == [[20000]]

    bot.send("deshacer")   # préstamo (planilla + archivo) y el gasto del mismo mensaje
    assert col_values(bot.service, maria, "principal!B13") == [[0]]
    assert col_values(bot.service, bot.session().active_sheet_id, "A11:D11") == []


def test_worker_file_full_keeps_daily_entry_and_warns(bot):
    bot.send("hoja 24-11-2026")
    file_id = bot.drive.add_worker("pedro")
    bot.service.files[file_id].sheets["principal"]["cells"][(3, 123)] = 29
    responses = bot.send("trabajador 5000 pedro")
    assert responses[0] == "Préstamo registrado: $5.000 - pedro"
    assert "ya tiene sus 16 vales ocupados" in responses[1]
    assert bot.service.files[file_id].raw("principal!B30") == "=SUM(B13:B29)"


# ----------------------------------------------------------------------
# Nómina
# ----------------------------------------------------------------------
def _loans(bot, name, *amounts):
    for amount in amounts:
        bot.send(f"trabajador {amount} {name}")


def test_nomina_archives_period_and_undo_restores_it(bot):
    bot.send("hoja 24-11-2026")
    _loans(bot, "pedro", 10000, 15000)
    file_id = bot.drive.workers[0][0]
    book = bot.service.files[file_id]

    responses = bot.send("nomina 300000 pedro")
    assert responses[0] == "Pago de nómina registrado en planilla: $300.000 - pedro"
    assert "Suma de préstamos: $25.000" in responses[1]
    archive = next(t for t in book.sheets if t != "principal")
    assert responses[2] == f"✅ Nómina procesada: hoja '{archive}' creada y hoja principal limpiada."
    assert col_values(bot.service, file_id, f"{archive}!A4:B5") == [["24-11-2026", 10000], ["24-11-2026", 15000]]
    assert col_values(bot.service, file_id, "principal!A13:B14") == [["", 0], ["", 0]]
    assert book.raw("principal!C123") == 13

    bot.send("deshacer")
    assert list(book.sheets) == ["principal"]
    assert col_values(bot.service, file_id, "principal!A13:B14") == [["24-11-2026", 10000], ["24-11-2026", 15000]]
    assert book.raw("principal!C123") == 15
    assert col_values(bot.service, bot.session().active_sheet_id, "C13:D13") == []


def test_nomina_twice_same_day_uses_unique_archive_name(bot):
    bot.send("hoja 24-11-2026")
    _loans(bot, "pedro", 1000)
    file_id = bot.drive.workers[0][0]
    bot.send("nomina 100 pedro")
    responses = bot.send("retiro 200 nomina de pedro")
    assert responses[0] == "Retiro registrado: $200 - nomina de pedro"
    assert responses[-1].endswith("(2)' creada y hoja principal limpiada.")
    assert len(bot.service.files[file_id].sheets) == 3


def test_nomina_undo_skips_restore_when_new_loans_exist(bot):
    bot.send("hoja 24-11-2026")
    _loans(bot, "pedro", 1000)
    bot.send("nomina 100 pedro")
    file_id = bot.drive.workers[0][0]
    # Otro admin registra un vale nuevo después de la nómina.
    bot.session("998").set_active_sheet(bot.session().active_sheet_id, "24-11-2026")
    bot.send("trabajador 500 pedro", phone="998")
    response = bot.send("deshacer")[0]
    assert "recibió vales nuevos después de la nómina" in response
    assert col_values(bot.service, file_id, "principal!B13") == [[500]]


def test_nomina_with_principal_sheet_id_zero_and_other_sheet_first(bot):
    bot.send("hoja 24-11-2026")
    _loans(bot, "pedro", 1000)
    file_id = bot.drive.workers[0][0]
    book = bot.service.files[file_id]
    # Una hoja archivada quedó de primera en el orden; "principal" tiene sheetId 0.
    book.sheets = {"01-11-2026": {"id": 5, "cells": {}}, **book.sheets}
    responses = bot.send("nomina 100 pedro")
    assert "Suma de préstamos: $1.000" in responses[1]
    assert book.raw("principal!C123") == 13
    assert book.raw("01-11-2026!A1") == ""


# ----------------------------------------------------------------------
# Otros
# ----------------------------------------------------------------------
def test_unregistered_phone_gets_its_identifier(bot):
    responses = bot.send("gasto 5000 pan", phone="123")
    assert "Tu identificador es: 123" in responses[0]


def test_help_lists_all_movement_commands(bot):
    help_text = bot.send("instrucciones")[0]
    for command in ("gasto", "limpieza", "alimentacion", "trabajador", "nomina",
                    "administrador", "retiro", "inversion", "saldo", "efectivo",
                    "terminar_dia", "deshacer"):
        assert command in help_text
    assert "\n            " not in help_text   # sin la indentación del código fuente


def test_two_ambiguous_loans_in_one_message_ask_one_menu_after_the_other(bot):
    bot.send("hoja 24-11-2026")
    salon = bot.drive.add_worker("jose salon")
    panadero = bot.drive.add_worker("jose panadero")
    maria = bot.drive.add_worker("maria")
    bot.drive.add_worker("mariana")

    responses = bot.send("trabajador 1000 jose", "trabajador 2000 maria")
    # Se muestra solo el primer menú; el segundo llega al responder el primero.
    assert sum("Hay varios trabajadores" in r for r in responses) == 1
    assert "similar a 'jose'" in responses[1]

    responses = bot.send("2")
    assert responses[0] == "📄 Préstamo guardado en el archivo de 'jose panadero'."
    assert "similar a 'maria'" in responses[1]
    assert bot.send("1") == ["📄 Préstamo guardado en el archivo de 'maria'."]

    assert col_values(bot.service, panadero, "principal!B13") == [[1000]]
    assert col_values(bot.service, salon, "principal!B13") == [[0]]
    assert col_values(bot.service, maria, "principal!B13") == [[2000]]

    bot.send("deshacer")   # revierte los dos préstamos completos (planilla + archivos)
    assert col_values(bot.service, panadero, "principal!B13") == [[0]]
    assert col_values(bot.service, maria, "principal!B13") == [[0]]
    assert col_values(bot.service, bot.session().active_sheet_id, "C11:D12") == []


def test_invalid_menu_option_asks_again(bot):
    bot.send("hoja 24-11-2026")
    bot.drive.add_worker("jose salon")
    bot.drive.add_worker("jose panadero")
    bot.send("trabajador 1000 jose")
    responses = bot.send("9")
    assert responses[0] == "⚠️ Opción inválida: 9."
    assert "similar a 'jose'" in responses[1]
    assert bot.send("3") == [
        "👤 Se creó el archivo del trabajador 'jose'.",
        "📄 Préstamo guardado en el archivo de 'jose'.",
    ]


# ----------------------------------------------------------------------
# Menú sin responder: el comando se cancela completo
# ----------------------------------------------------------------------
CANCELLED = "⚠️ No escogiste ninguna opción del menú, así que se canceló {} y se borró de la planilla."


def _two_joses(bot):
    bot.send("hoja 24-11-2026")
    return bot.drive.add_worker("jose salon"), bot.drive.add_worker("jose panadero")


def test_unanswered_loan_menu_cancels_the_loan(bot):
    salon, panadero = _two_joses(bot)
    bot.send("trabajador 1000 jose", "gasto 500 pan")
    responses = bot.send("gasto 300 sal")
    assert responses == [CANCELLED.format("'trabajador 1000 jose'"), "Gasto registrado: $300 - sal"]
    sheet = bot.session().active_sheet_id
    assert col_values(bot.service, sheet, "C11:D11") == []                 # préstamo borrado
    assert col_values(bot.service, sheet, "A11:B12") == [["pan", 500], ["sal", 300]]
    assert col_values(bot.service, salon, "principal!B13") == [[0]]
    assert col_values(bot.service, panadero, "principal!B13") == [[0]]
    assert not bot.session().pending_selections


def test_cancelled_menu_then_undo_in_the_same_message(bot):
    _two_joses(bot)
    bot.send("trabajador 1000 jose", "gasto 500 pan")
    assert bot.send("deshacer") == [
        CANCELLED.format("'trabajador 1000 jose'"), "✅ Se deshizo: gasto 500 pan."]
    assert col_values(bot.service, bot.session().active_sheet_id, "A11:D11") == []


def test_message_without_commands_also_cancels_the_menu(bot):
    _two_joses(bot)
    bot.send("nomina 1000 jose")
    responses = bot.send()          # mensaje sin comandos (ej. "jajaja")
    assert responses[0] == CANCELLED.format("'nomina 1000 jose'")
    assert "No encontré ningún comando" in responses[1]
    assert col_values(bot.service, bot.session().active_sheet_id, "C11:D11") == []


def test_unanswered_retiro_nomina_menu_cancels_the_withdrawal(bot):
    _two_joses(bot)
    responses = bot.send("retiro 9000 nomina jose")
    assert responses[0] == "Retiro registrado: $9.000 - nomina jose"
    bot.send("gasto 1 sal")
    assert col_values(bot.service, bot.session().active_sheet_id, "C39:E39") == []
    assert bot.session().undo_snapshot.description == "gasto 1 sal"


def test_two_unanswered_menus_are_both_cancelled(bot):
    _two_joses(bot)
    bot.drive.add_worker("rosa alta")
    bot.drive.add_worker("rosa baja")
    bot.send("trabajador 1000 jose", "trabajador 2000 rosa")
    responses = bot.send("gasto 1 sal")
    assert responses[0] == CANCELLED.format("'trabajador 1000 jose'; 'trabajador 2000 rosa'")
    assert col_values(bot.service, bot.session().active_sheet_id, "C11:D12") == []


def test_answered_menu_is_not_cancelled(bot):
    salon, _ = _two_joses(bot)
    bot.send("trabajador 1000 jose")
    menu = bot.send("9")[1]
    option = next(line.split(".")[0] for line in menu.splitlines() if line.endswith("jose salon"))
    bot.send(option)
    bot.send("gasto 1 sal")          # ya no hay menú pendiente: nada se cancela
    assert col_values(bot.service, bot.session().active_sheet_id, "C11:D11") == [["jose", 1000]]
    assert col_values(bot.service, salon, "principal!B13") == [[1000]]


# ----------------------------------------------------------------------
# corregir_saldos
# ----------------------------------------------------------------------
def _b42(bot, name):
    return bot.service.files[bot.drive.planillas[name]].raw("B42")


def test_corregir_saldos_rechains_all_following_sheets_and_undo(bot):
    bot.send("hoja 22-11-2026", "efectivo 1000")
    bot.send("hoja 23-11-2026", "efectivo 500")          # B42 = 1000 -> B58 = 1500
    bot.send("segunda planilla", "retiro 200 banco")      # B42 = 1500 -> B58 = 1300
    bot.send("hoja 25-11-2026")                           # falta el 24: B42 = 0
    assert [_b42(bot, n) for n in ("23-11-2026", "23-11-2026-2", "25-11-2026")] == [1000, 1500, 0]

    bot.send("hoja 22-11-2026", "efectivo 4000")          # se corrige el día 22
    response = bot.send("corregir_saldos")[0]
    assert response == (
        "🔄 Saldos corregidos desde '22-11-2026':\n"
        "• 23-11-2026: $1.000 → $4.000\n"
        "• 23-11-2026-2: $1.500 → $4.500\n"
        "• 25-11-2026: $0 → $4.300"
    )
    assert [_b42(bot, n) for n in ("23-11-2026", "23-11-2026-2", "25-11-2026")] == [4000, 4500, 4300]
    assert _b42(bot, "22-11-2026") == 0                   # la seleccionada no se toca

    assert bot.send("deshacer") == ["✅ Se deshizo: corregir_saldos."]
    assert [_b42(bot, n) for n in ("23-11-2026", "23-11-2026-2", "25-11-2026")] == [1000, 1500, 0]


def test_corregir_saldos_when_already_correct_or_nothing_after(bot):
    bot.send("hoja 22-11-2026", "efectivo 1000")
    bot.send("hoja 23-11-2026")
    assert bot.send("corregir_saldos") == [
        "No hay planillas posteriores a '23-11-2026': no hay saldos que corregir."]
    bot.send("hoja 22-11-2026")
    assert bot.send("corregir saldos") == [
        "✅ Los saldos de las 1 planilla(s) posteriores a '22-11-2026' ya estaban bien."]
    assert bot.send("deshacer") == ["✅ Se deshizo: efectivo 1000."]   # no registró nada


def test_corregir_saldos_stops_at_non_numeric_total(bot):
    bot.send("hoja 22-11-2026")
    bot.send("hoja 23-11-2026")
    bot.send("hoja 24-11-2026")
    bot.service.files[bot.drive.planillas["23-11-2026"]].sheets["Hoja 1"]["cells"][(2, 58)] = "#REF!"
    bot.send("hoja 22-11-2026", "efectivo 700")
    response = bot.send("corregir_saldos")[0]
    assert response.startswith("🔄 Saldos corregidos desde '22-11-2026':\n• 23-11-2026: $0 → $700")
    assert "El saldo total de '23-11-2026' no es un número (#REF!)" in response
    assert _b42(bot, "24-11-2026") == 0


def test_corregir_saldos_requires_active_sheet(bot):
    assert bot.send("corregir_saldos")[0].startswith("⚠️ No hay una planilla activa")
