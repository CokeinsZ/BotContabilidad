"""Comando para recalcular los saldos de las planillas posteriores."""
from accounting.commands.base import Command, CommandContext
from accounting.money import format_amount
from accounting.sheet_naming import parse_sheet_name
from accounting.undo import CellStep
from config.log import log_warning
from sheets.sheets_client import FORMULA, same_value


class CorrectBalancesCommand(Command):
    """`corregir_saldos`: re-encadena el saldo desde la planilla seleccionada.

    Al crear una planilla, su saldo efectivo (B42) se copia del saldo total
    (B58) de la anterior; si después se corrige una planilla vieja, las
    siguientes quedan con el saldo desactualizado. Este comando recorre, en
    orden cronológico, TODAS las planillas posteriores a la seleccionada
    (también las adicionales del mismo día) hasta la última creada, y pone
    en cada una B42 = B58 de la anterior (ya recalculado).

    La planilla seleccionada no se modifica: es el punto de partida. Si entre
    dos planillas faltan días, el saldo pasa de la última planilla existente
    a la siguiente. Todo el cambio es deshacible con 'deshacer'.
    """

    name = "corregir_saldos"
    aliases = ("corregir saldos", "corregir_saldo", "corregir saldo", "recalcular_saldos")

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if error := self.require_active_sheet(ctx):
            return error
        start_name = ctx.session.active_sheet_name or ""
        start = parse_sheet_name(start_name)
        if start is None:
            return f"⚠️ La planilla activa '{start_name}' no tiene un nombre de fecha válido."

        files = ctx.drive.list_planillas_from(ctx.business.sheets_folder_id, start[0])
        if files is None:
            return "⚠️ No se pudieron listar las planillas en Drive. Intenta de nuevo."
        following = sorted(
            (key, file_id, name)
            for file_id, name in files
            if (key := parse_sheet_name(name)) is not None and key > start
        )
        if not following:
            return f"No hay planillas posteriores a '{start_name}': no hay saldos que corregir."

        layout = ctx.sheets.layout
        cell = layout.generated_cash_cell
        previous_id, previous_name = ctx.session.active_sheet_id, start_name
        changes: list[tuple[str, object, object]] = []
        steps: list[CellStep] = []
        unchanged = 0
        problem = None

        for _key, file_id, name in following:
            total = ctx.sheets.get_value(previous_id, layout.total_cash_cell)
            if total is None or total == "":
                total = 0
            if isinstance(total, bool) or not isinstance(total, (int, float)):
                log_warning(
                    "corregir_saldos: saldo total no numérico",
                    f"sheet={previous_name!r} cell={layout.total_cash_cell} value={total!r}",
                )
                problem = (
                    f"⚠️ El saldo total de '{previous_name}' no es un número ({total}); "
                    f"la corrección se detuvo antes de '{name}'."
                )
                break

            with ctx.sheets.lock(file_id):
                current_values = ctx.sheets.get_values(file_id, [cell], FORMULA)
                if current_values is None:
                    problem = f"⚠️ No se pudo leer '{name}'; la corrección se detuvo ahí."
                    break
                rows = current_values.get(cell, [])
                current = rows[0][0] if rows and rows[0] else ""
                if same_value(current, total):
                    unchanged += 1
                elif ctx.sheets.set_values(file_id, {cell: [[total]]}):
                    steps.append(CellStep(sheet_id=file_id, cell=cell, written_value=total, restore_value=current))
                    changes.append((name, current, total))
                else:
                    problem = f"⚠️ No se pudo escribir el saldo de '{name}'; la corrección se detuvo ahí."
                    break
            previous_id, previous_name = file_id, name

        if steps:
            ctx.undo.record(steps, description=self.name)

        lines = []
        if changes:
            lines.append(f"🔄 Saldos corregidos desde '{start_name}':")
            lines += [
                f"• {name}: {format_amount(old) if old != '' else 'vacío'} → {format_amount(new)}"
                for name, old, new in changes
            ]
        elif not problem:
            lines.append(
                f"✅ Los saldos de las {unchanged} planilla(s) posteriores a '{start_name}' ya estaban bien."
            )
        if unchanged and changes:
            lines.append(f"{unchanged} planilla(s) ya estaban bien.")
        if problem:
            lines.append(problem)
        return "\n".join(lines)
