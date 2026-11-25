"""Comando de resumen del día."""
from accounting.commands.base import Command, CommandContext
from accounting.money import format_amount
from config.log import log_warning


class SummaryCommand(Command):
    """`terminar_dia`: resumen de ingresos, gastos y saldo de la planilla."""

    name = "terminar_dia"
    aliases = ("resumen",)

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if error := self.require_active_sheet(ctx):
            return error

        sheet_id = ctx.session.active_sheet_id
        totals = ctx.sheets.get_daily_totals(sheet_id)
        if totals is None:
            log_warning(
                "comando 'terminar_dia' no pudo obtener totales",
                f"business_id={ctx.business.id} sheet_id={sheet_id} "
                f"sheet_name={ctx.session.active_sheet_name!r} "
                f"-> ver log previo de SheetsClient",
            )
            return "⚠️ No se pudieron obtener los totales de la planilla."

        return (
            f'Link a la planilla: "https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"\n'
            "\n"
            f"Resumen de la planilla {ctx.session.active_sheet_name or ''}:\n"
            f"    - Gastos totales del día: {format_amount(totals.total_expenses)}\n"
            f"    - Efectivo del día: {format_amount(totals.day_cash)}\n"
            f"    - Ventas totales del día: {format_amount(totals.total_sales)}\n"
            f"    - Saldo previo: {format_amount(totals.previous_balance)}\n"
            f"    - Saldo total: {format_amount(totals.total_balance)}"
        )
