"""Comandos de manejo de efectivo: retiros, saldo, efectivo e inversiones."""
from abc import abstractmethod
from typing import ClassVar

from accounting.commands.base import Command, CommandContext
from accounting.commands.region_entry import RegionEntryCommand
from accounting.session_manager import UndoSnapshot


class WithdrawalCommand(RegionEntryCommand):
    """`retiro <monto> <descripción>`: sacar dinero de la caja."""

    name = "retiro"
    aliases = ("r",)
    region_attr = "withdraw_region"
    success_label = "Retiro registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto y la descripción del retiro."
    invalid_amount_message = "⚠️ El monto del retiro debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 2 else None

    def build_row(self, args: list[str]) -> list:
        amount = self.parse_amount(args[0])
        description = " ".join(args[1:])
        # La región de retiros usa las columnas C:E con la D vacía.
        return [description, "", amount]


class InvestmentCommand(RegionEntryCommand):
    """`inversion <monto> <descripción>`: inversiones en el negocio."""

    name = "inversion"
    aliases = ("inversiones", "inv")
    region_attr = "investment_region"
    success_label = "Inversión registrada"
    missing_args_message = "⚠️ Debes proporcionar el monto y la descripción de la inversión."
    invalid_amount_message = "⚠️ El monto de la inversión debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 2 else None

    def build_row(self, args: list[str]) -> list:
        amount = self.parse_amount(args[0])
        description = " ".join(args[1:])
        return [description, amount]


class FixedCellCommand(Command):
    """Base para comandos que sobrescriben una celda fija (deshacibles)."""

    cell_attr: ClassVar[str]
    success_label: ClassVar[str]
    missing_args_message: ClassVar[str]
    invalid_amount_message: ClassVar[str]
    empty_value: ClassVar[object] = ""

    @abstractmethod
    def parse_value(self, args: list[str]):
        """Convierte los argumentos en el valor a escribir."""

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if error := self.require_active_sheet(ctx):
            return error
        if len(args) < 1:
            return self.missing_args_message

        try:
            value = self.parse_value(args)
        except ValueError:
            return self.invalid_amount_message

        sheet_id = ctx.session.active_sheet_id
        cell = getattr(ctx.sheets.layout, self.cell_attr)

        previous_value = ctx.sheets.get_value(sheet_id, cell)
        if not ctx.sheets.set_values(sheet_id, {cell: [[value]]}):
            return "⚠️ No se pudo registrar el valor en la planilla."

        ctx.session.undo_snapshot = UndoSnapshot.single(
            description=" ".join([self.name, *args]),
            sheet_id=sheet_id,
            cell=cell,
            restore_value=(
                previous_value if previous_value is not None else self.empty_value
            ),
        )
        return f"{self.success_label}: {value}"


class BalanceCommand(FixedCellCommand):
    """`saldo <monto>`: informa cuánto dinero físico hay en caja."""

    name = "saldo"
    aliases = ("saldos", "s")
    cell_attr = "generated_cash_cell"
    success_label = "Saldo registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del saldo."
    invalid_amount_message = "⚠️ El monto del saldo debe ser un número válido."

    def parse_value(self, args: list[str]):
        return self.parse_amount(args[0])


class CashCommand(FixedCellCommand):
    """`efectivo <monto>`: dinero de ventas del día."""

    name = "efectivo"
    aliases = ("e",)
    cell_attr = "day_cash_cell"
    success_label = "Efectivo registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del efectivo."
    invalid_amount_message = "⚠️ El monto del efectivo debe ser un número válido."
    empty_value = 0

    def parse_value(self, args: list[str]):
        return self.parse_amount(args[0])
