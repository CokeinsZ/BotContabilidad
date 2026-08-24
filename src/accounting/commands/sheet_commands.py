"""Comando para crear o seleccionar la planilla diaria."""
from datetime import datetime, timedelta

from accounting.commands.base import Command, CommandContext


class SelectSheetCommand(Command):
    """`hoja <dd-mm-aaaa>`: selecciona o crea la planilla del día.

    Al crear una planilla nueva escribe en UNA sola llamada por lotes:
      - A2: nombre del business (reemplaza el de la plantilla duplicada)
      - B6: nombre del administrador que ejecuta el comando
      - B7: fecha de la planilla
      - B42: saldo final de la planilla del día anterior (si existe)
    """

    name = "hoja"
    aliases = ("planilla", "h")

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if not args:
            return "⚠️ Debes proporcionar el nombre de la planilla."

        sheet_name = args[0]
        try:
            current_date = datetime.strptime(sheet_name, "%d-%m-%Y")
        except ValueError:
            return f"⚠️ Formato de fecha inválido: '{sheet_name}'. Usa dd-mm-aaaa."

        folder_id = ctx.business.sheets_folder_id

        # 1. Si ya existe, solo se selecciona (2 llamadas a Drive como máximo).
        existing_id = ctx.drive.find_sheet_by_name(folder_id, sheet_name)
        if existing_id:
            ctx.session.set_active_sheet(existing_id, sheet_name)
            return f"Planilla '{sheet_name}' seleccionada."

        # 2. Crear duplicando la plantilla en la carpeta del mes.
        duplicated = ctx.drive.duplicate_template(folder_id, sheet_name)
        if duplicated is None:
            return f"⚠️ No se pudo crear o encontrar la planilla: '{sheet_name}'."
        sheet_id, _ = duplicated

        # 3. Cargar el saldo final de la planilla del día anterior (si existe).
        previous_day_name = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")
        previous_sheet_id = ctx.drive.find_sheet_by_name(folder_id, previous_day_name)

        layout = ctx.sheets.layout
        updates = {
            layout.business_name_cell: [[ctx.business.name]],
            layout.admin_name_cell: [[ctx.administrator.name]],
            layout.date_cell: [[sheet_name]],
        }
        warning = None
        if previous_sheet_id:
            previous_balance = ctx.sheets.get_value(
                previous_sheet_id, layout.total_cash_cell
            )
            updates[layout.generated_cash_cell] = [
                [previous_balance if previous_balance is not None else 0]
            ]
        else:
            warning = (
                f"No existe una planilla para el día anterior: '{previous_day_name}',"
                "\npor lo tanto no se pudo cargar el balance anterior."
            )

        # 4. Inicializar la planilla nueva con una sola escritura por lotes.
        if not ctx.sheets.set_values(sheet_id, updates):
            return f"⚠️ La planilla '{sheet_name}' se creó pero no pudo inicializarse."

        ctx.session.set_active_sheet(sheet_id, sheet_name)

        message = f"Planilla '{sheet_name}' seleccionada."
        return f"{warning}\n\n{message}" if warning else message
