"""Comando para deshacer la última acción del usuario."""
from accounting.commands.base import Command, CommandContext


class UndoCommand(Command):
    """`deshacer`: revierte el último comando que modificó la planilla."""

    name = "deshacer"
    aliases = ("undo",)

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        snapshot = ctx.session.undo_snapshot
        if snapshot is None:
            return "⚠️ No hay un comando para deshacer."

        if snapshot.region is not None:
            success = ctx.sheets.undo_last_entry(snapshot.sheet_id, snapshot.region)
        elif snapshot.cell is not None:
            success = ctx.sheets.set_values(
                snapshot.sheet_id, {snapshot.cell: [[snapshot.restore_value]]}
            )
        else:
            success = False

        if success:
            ctx.session.undo_snapshot = None
            return f"✅ Se deshizo el último comando: {snapshot.description}."

        return "⚠️ No se pudo deshacer el último comando."
