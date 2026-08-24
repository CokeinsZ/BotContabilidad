"""Comando de resumen del día."""
from accounting.commands.base import Command, CommandContext


class SummaryCommand(Command):
    """`terminar_dia`: resumen de ingresos, gastos y saldo de la planilla."""

    name = "terminar_dia"
    aliases = ("resumen",)

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if error := self.require_active_sheet(ctx):
            return error

        sheet_id = ctx.session.active_sheet_id
        totals = ctx.sheets.get_daily_totals(sheet_id)
        if not totals:
            return "⚠️ No se pudieron obtener los totales de la planilla."

        total_expenses, day_cash, total_sells, previous_cash, total_cash = totals
        return (
            f'Link a la planilla: "https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"\n'
            "\n"
            "Resumen de la planilla:\n"
            f"    - Gastos totales del día: {total_expenses}\n"
            f"    - Efectivo del día: {day_cash}\n"
            f"    - Ventas totales del día: {total_sells}\n"
            f"    - Saldo previo: {previous_cash}\n"
            f"    - Saldo total: {total_cash}"
        )
