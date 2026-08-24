"""Base para comandos que agregan una fila a una región de la planilla."""
from abc import abstractmethod
from typing import ClassVar

from accounting.commands.base import Command, CommandContext
from accounting.session_manager import UndoSnapshot


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

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if error := self.require_active_sheet(ctx):
            return error
        if error := self.validate_args(args):
            return error

        try:
            row = self.build_row(args)
        except ValueError:
            return self.invalid_amount_message

        sheet_id = ctx.session.active_sheet_id
        region = getattr(ctx.sheets.layout, self.region_attr)

        if not ctx.sheets.append_to_region(sheet_id, region, row):
            return "⚠️ No se pudo registrar el movimiento en la planilla."

        ctx.session.undo_snapshot = UndoSnapshot(
            sheet_id=sheet_id, description=self.describe(args), region=region
        )
        return self.success_message(args)

    def success_message(self, args: list[str]) -> str:
        amount = self.parse_amount(args[0])
        description = " ".join(args[1:])
        if description:
            return f"{self.success_label}: {amount} - {description}"
        return f"{self.success_label}: {amount}"
