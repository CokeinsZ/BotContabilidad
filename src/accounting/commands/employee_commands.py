"""Comandos de pagos a trabajadores y vales del administrador."""
from accounting.commands.region_entry import RegionEntryCommand


class WorkerPaymentCommand(RegionEntryCommand):
    """`trabajador <monto> <nombre>`: sueldos o adelantos a personas."""

    name = "trabajador"
    aliases = ("trabajadores", "t")
    region_attr = "worker_region"
    success_label = "Pago registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto y el nombre del trabajador."
    invalid_amount_message = "⚠️ El monto del pago debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 2 else None

    def build_row(self, args: list[str]) -> list:
        amount = self.parse_amount(args[0])
        worker_name = " ".join(args[1:])
        return [worker_name, amount]


class AdminPaymentCommand(RegionEntryCommand):
    """`administrador <monto>`: vales para el administrador/dueño."""

    name = "administrador"
    aliases = ("admin",)
    region_attr = "admin_region"
    success_label = "Pago administrativo registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del pago."
    invalid_amount_message = "⚠️ El monto del pago debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 1 else None

    def build_row(self, args: list[str]) -> list:
        return [self.parse_amount(args[0])]
