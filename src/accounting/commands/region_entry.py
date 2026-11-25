"""Base para comandos que agregan una fila a una región de la planilla."""
from abc import abstractmethod
from typing import ClassVar

from accounting.commands.base import Command, CommandContext
from accounting.money import format_amount
from accounting.undo import RegionEntryStep
from config.log import log_error, log_warning
from sheets.sheets_client import RegionFullError


class RegionEntryCommand(Command):
    """Registra una fila en una región dinámica (deshacible).

    Las subclases solo declaran la región del layout, los mensajes y cómo
    construir la fila a partir de los argumentos (OCP: un nuevo tipo de
    movimiento es una subclase de pocas líneas, sin tocar código existente).
    """

    region_attr: ClassVar[str]
    success_label: ClassVar[str]
    missing_args_message: ClassVar[str]
    invalid_amount_message: ClassVar[str]

    @abstractmethod
    def build_row(self, args: list[str]) -> list:
        """Construye la fila a escribir. Puede lanzar ValueError."""

    @abstractmethod
    def validate_args(self, args: list[str]) -> str | None:
        """Devuelve un mensaje de error si los argumentos no son válidos."""

    def describe(self, args: list[str]) -> str:
        return " ".join([self.name, *args])

    def record(self, ctx: CommandContext, args: list[str]) -> tuple[bool, str]:
        """Escribe la fila y registra el paso de deshacer.

        Devuelve (éxito, mensaje para el usuario).
        """
        if error := self.require_active_sheet(ctx):
            return False, error
        if error := self.validate_args(args):
            return False, error

        try:
            row_values = self.build_row(args)
        except ValueError as error:
            log_error(
                f"comando '{self.name}' con monto inválido",
                error,
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"sheet_id={ctx.session.active_sheet_id} "
                f"sheet_name={ctx.session.active_sheet_name!r} args={args}",
            )
            return False, self.invalid_amount_message

        sheet_id = ctx.session.active_sheet_id
        region = getattr(ctx.sheets.layout, self.region_attr)

        try:
            row = ctx.sheets.append_to_region(sheet_id, region, row_values)
        except RegionFullError:
            return False, self.region_full_message(region)
        except Exception as error:
            log_error(
                f"comando '{self.name}' falló escribiendo en la planilla (excepción)",
                error,
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"sheet_id={sheet_id} sheet_name={ctx.session.active_sheet_name!r} "
                f"region={region} row={row_values} args={args}",
            )
            return False, "⚠️ No se pudo registrar el movimiento en la planilla."

        if row is None:
            # El detalle del porqué ya lo logueó SheetsClient; aquí se agrega
            # el contexto del comando para correlacionar con el mensaje del usuario.
            log_warning(
                f"comando '{self.name}' no pudo registrar el movimiento",
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"sheet_id={sheet_id} sheet_name={ctx.session.active_sheet_name!r} "
                f"region={region} row={row_values} args={args} "
                f"-> ver log previo de SheetsClient para la causa raíz",
            )
            return False, "⚠️ No se pudo registrar el movimiento en la planilla."

        ctx.undo.record(
            [RegionEntryStep(sheet_id=sheet_id, region=region, row=row, values=row_values)],
            description=self.describe(args),
        )
        return True, self.success_message(args)

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        _ok, message = self.record(ctx, args)
        return message

    def success_message(self, args: list[str]) -> str:
        amount = format_amount(self.parse_amount(args[0]))
        description = " ".join(args[1:])
        if description:
            return f"{self.success_label}: {amount} - {description}"
        return f"{self.success_label}: {amount}"
