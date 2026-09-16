"""Comando para deshacer la última acción del usuario."""
from accounting.commands.base import Command, CommandContext
from config.log import log_error, log_warning


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
            try:
                if step.region is not None:
                    ok = ctx.sheets.undo_last_entry(step.sheet_id, step.region)
                elif step.cell is not None:
                    ok = ctx.sheets.set_values(step.sheet_id, {step.cell: [[step.restore_value]]})
                else:
                    ok = False
            except Exception as error:
                log_error(
                    "deshacer paso (excepción)",
                    error,
                    f"business_id={ctx.business.id} description={snapshot.description!r} "
                    f"sheet_id={step.sheet_id} region={step.region} cell={step.cell}",
                )
                ok = False
            if not ok:
                log_warning(
                    "deshacer paso falló",
                    f"business_id={ctx.business.id} description={snapshot.description!r} "
                    f"sheet_id={step.sheet_id} region={step.region} cell={step.cell} "
                    f"-> ver log previo de SheetsClient",
                )
                success = False

        if success:
            ctx.session.undo_snapshot = None
            return f"✅ Se deshizo el último comando: {snapshot.description}."

        return "⚠️ No se pudo deshacer el último comando completamente."
