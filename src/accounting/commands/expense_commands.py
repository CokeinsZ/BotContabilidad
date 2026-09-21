"""Comandos de gastos: insumos, limpieza y alimentación."""
from accounting.commands.region_entry import RegionEntryCommand


class ExpenseCommand(RegionEntryCommand):
    """`gasto <monto> <descripción>`: compras de insumos/mercancía."""

    name = "gasto"
    aliases = ("g",)
    region_attr = "expense_region"
    success_label = "Gasto registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto y la descripción del gasto."
    invalid_amount_message = "⚠️ El monto del gasto debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 2 else None

    def build_row(self, args: list[str]) -> list:
        amount = self.parse_amount(args[0])
        description = " ".join(args[1:])
        return [description, amount]


class CleaningExpenseCommand(RegionEntryCommand):
    """`limpieza <monto>`: gastos de productos de aseo/limpieza."""

    name = "limpieza"
    aliases = ("aseo", "aseos", "l")
    region_attr = "cleaning_region"
    success_label = "Gasto de limpieza registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del gasto."
    invalid_amount_message = "⚠️ El monto del gasto debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 1 else None

    def build_row(self, args: list[str]) -> list:
        return [self.parse_amount(args[0])]


class FeedingExpenseCommand(RegionEntryCommand):
    """`alimentacion <monto>`: gastos de alimentación del personal."""

    name = "alimentacion"
    aliases = ("alimentaciones", "comida", "a")
    region_attr = "feeding_region"
    success_label = "Gasto de alimentación registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del gasto."
    invalid_amount_message = "⚠️ El monto del gasto debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 1 else None

    def build_row(self, args: list[str]) -> list:
        return [self.parse_amount(args[0])]
