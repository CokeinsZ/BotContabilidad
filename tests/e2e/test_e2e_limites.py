"""E2E: límites de cada sección de la planilla diaria."""
from e2e_support import BotUser, Run


def send_batches(user: BotUser, command: str, amounts: list[int], suffix: str = "", size: int = 8) -> list[str]:
    """Envía `command <monto> <suffix>` en mensajes de `size` comandos."""
    replies = []
    for start in range(0, len(amounts), size):
        chunk = amounts[start:start + size]
        text = ", ".join(f"{command} {a}{' ' + suffix if suffix else ''}" for a in chunk)
        batch = user.send(text)
        assert len(batch) == len(chunk), f"DeepSeek/bot no devolvió un resultado por comando: {batch}"
        replies += batch
    return replies


SECTIONS = {
    # comando: (montos que caben, sufijo, columna de montos, celda de encabezado siguiente)
    "gasto": (list(range(1001, 1025)), "insumo"),          # A:B 11-34 (24)
    "administrador": (list(range(2601, 2610)), ""),        # E 26-34 (9)
    "retiro": (list(range(3901, 3922)), "banco"),          # C:E 39-59 (21)
    "inversion": (list(range(2901, 2907)), "horno"),       # C:D 29-34 (6)
    "limpieza": (list(range(1101, 1109)), ""),             # E 11-18 (8)
    "alimentacion": (list(range(2001, 2006)), ""),         # E 20-24 (5)
}


def test_llenar_todas_las_secciones_y_rechazar_el_excedente(run: Run, admin: BotUser):
    google = run.google
    admin.send("hoja 01-03-2026")

    for command, (amounts, suffix) in SECTIONS.items():
        replies = send_batches(admin, command, amounts, suffix)
        assert not any("⚠️" in r for r in replies), replies

    # Un comando más por sección: todos rechazados, ninguno escribe.
    overflow = admin.send(
        "gasto 9999 extra, administrador 9999, retiro 9999 extra, "
        "inversion 9999 extra, limpieza 9999 y alimentacion 9999"
    )
    assert len(overflow) == 6
    for label, reply in zip(
        ["compras proveedores", "administrador", "retiros", "inversiones", "aseo", "alimentación"],
        overflow,
    ):
        assert f"La sección '{label}' de la planilla está llena" in reply

    sheet = run.planilla("01-03-2026")
    g = SECTIONS
    assert google.column(sheet, "B11:B34") == g["gasto"][0]
    assert google.column(sheet, "E26:E34") == g["administrador"][0]
    assert google.column(sheet, "E39:E59") == g["retiro"][0]
    assert google.column(sheet, "C39:C59") == ["banco"] * 21
    assert google.column(sheet, "D29:D34") == g["inversion"][0]
    assert google.column(sheet, "E11:E18") == g["limpieza"][0]
    assert google.column(sheet, "E20:E24") == g["alimentacion"][0]
    assert 9999 not in google.column(sheet, "B11:B37") + google.column(sheet, "E10:E60")

    # Encabezados, etiquetas y fórmulas de la plantilla siguen intactos.
    fixed = google.cells(
        sheet, "A35", "B35", "C27", "D27", "C28", "D35", "E19", "E25", "E35",
        "A38", "B38", "C60", "E60", "A58", "B58", render="FORMULA",
    )
    assert fixed == {
        "A35": "TOTALES", "B35": "=SUM(B11:B34)", "C27": "Total Trabajadores",
        "D27": "=SUM(D11:D26)", "C28": "INVERSIONES DEL DIA", "D35": "=SUM(D29:D34)",
        "E19": "ALIMENT.", "E25": "ADMINISTRADOR", "E35": "=SUM(E26:E34)",
        "A38": "TOTAL GASTOS  DIA", "B38": "=B35+D27+D35+E35+SUM(E10:E18)+SUM(E20:E24)",
        "C60": "TOTAL", "E60": "=SUM(E39:E59)", "A58": "SALDO TOTAL", "B58": "=B39+B42-E60",
    }

    # Contadores en su máximo y totales calculados por la planilla.
    counters = google.cells(sheet, "C135", "C137", "C138", "C139", "C140", "C141")
    assert counters == {"C135": 35, "C137": 35, "C138": 60, "C139": 35, "C140": 19, "C141": 25}
    totals = google.cells(sheet, "B38", "E60", "B58")
    expected_expenses = sum(sum(g[c][0]) for c in ("gasto", "administrador", "inversion", "limpieza", "alimentacion"))
    assert totals == {"B38": expected_expenses, "E60": sum(g["retiro"][0]), "B58": -sum(g["retiro"][0])}

    # El mensaje rechazado no registró nada: deshacer revierte el último
    # mensaje que SÍ escribió (las 5 alimentaciones) y libera la sección.
    assert admin.send("deshacer")[0].startswith("✅ Se deshizo: alimentacion 2001")
    assert google.column(sheet, "E20:E24") == [""] * 5
    assert google.value(sheet, "C141") == 20
    assert admin.send("alimentacion 2099") == ["Gasto de alimentación registrado: $2.099"]
    assert google.value(sheet, "E20") == 2099


def test_seccion_llena_libera_fila_cuando_otro_admin_deshace(run: Run, admin: BotUser, admin2: BotUser):
    """Deshacer en una sección llena compacta las filas y vuelve a dar espacio."""
    google = run.google
    admin.send("hoja 02-03-2026")
    admin2.send("hoja 02-03-2026")
    sheet = run.planilla("02-03-2026")

    admin.send("limpieza 1")
    admin2.send("limpieza 2, limpieza 3, limpieza 4, limpieza 5, limpieza 6, limpieza 7 y limpieza 8")
    assert google.column(sheet, "E11:E18") == [1, 2, 3, 4, 5, 6, 7, 8]
    assert "está llena" in admin.send("limpieza 99")[0]

    # El admin 1 deshace su "limpieza 1" (el rechazo no cuenta): se borra SU
    # fila y las 7 del admin 2 suben una posición.
    assert admin.send("deshacer") == ["✅ Se deshizo: limpieza 1."]
    assert google.column(sheet, "E11:E18") == [2, 3, 4, 5, 6, 7, 8, ""]
    assert google.value(sheet, "C140") == 18
    assert google.value(sheet, "E19") == "ALIMENT."

    assert admin.send("limpieza 9") == ["Gasto de limpieza registrado: $9"]
    assert google.column(sheet, "E11:E18") == [2, 3, 4, 5, 6, 7, 8, 9]

    # El admin 2 deshace sus 7 filas aunque ahora estén en otra posición.
    assert admin2.send("deshacer")[0].startswith("✅ Se deshizo: limpieza 2")
    assert google.column(sheet, "E11:E18") == [9, "", "", "", "", "", "", ""]
    assert google.value(sheet, "C140") == 12
