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

        success = True
        for step in snapshot.steps:
            if step.region is not None:
                ok = ctx.sheets.undo_last_entry(step.sheet_id, step.region)
            elif step.cell is not None:
                ok = ctx.sheets.set_values(step.sheet_id, {step.cell: [[step.restore_value]]})
            else:
                ok = False
            if not ok:
                success = False

        if success:
            ctx.session.undo_snapshot = None
            return f"✅ Se deshizo el último comando: {snapshot.description}."

        return "⚠️ No se pudo deshacer el último comando completamente."
