"""Comando para deshacer el último mensaje del usuario (todos sus comandos)."""
from accounting.commands.base import Command, CommandContext
from accounting.undo import Outcome, UndoSnapshot, UndoStep
from config.log import log_error, log_warning


class UndoCommand(Command):
    """`deshacer`: revierte TODO lo que hizo el último mensaje.

    Si el mensaje actual ya ejecutó comandos antes de `deshacer` (ej:
    "gasto 5000 pan y deshaz eso"), se revierten esos; si no, se revierte
    el mensaje anterior completo. Los pasos se deshacen en orden inverso.
    """

    name = "deshacer"
    aliases = ("undo",)

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        # Deshacer invalida cualquier menú pendiente (ej: elegir trabajador
        # para un préstamo que se acaba de revertir).
        ctx.session.pending_selections.clear()

        if ctx.undo.has_steps:
            snapshot = ctx.undo.to_snapshot()
            ctx.undo.clear()
            in_current_message = True
        else:
            snapshot = ctx.session.undo_snapshot
            in_current_message = False
        if snapshot is None or not snapshot.steps:
            return "⚠️ No hay un comando para deshacer."

        failed: list[UndoStep] = []
        notes: list[str] = []
        for step in reversed(snapshot.steps):
            try:
                result = step.undo(ctx.sheets)
            except Exception as error:
                log_error(
                    "deshacer paso (excepción)",
                    error,
                    f"business_id={ctx.business.id} description={snapshot.description!r} step={step}",
                )
                failed.append(step)
                continue
            if result.outcome is Outcome.FAILED:
                log_warning(
                    "deshacer paso falló",
                    f"business_id={ctx.business.id} description={snapshot.description!r} "
                    f"step={step} -> ver log previo de SheetsClient",
                )
                failed.append(step)
            elif result.note:
                notes.append(result.note)

        # Los pasos fallidos quedan para reintentar con otro 'deshacer'.
        remaining = (
            UndoSnapshot([snapshot.description], list(reversed(failed))) if failed else None
        )
        if in_current_message:
            if remaining:
                ctx.undo.record(remaining.steps, remaining.description)
        else:
            ctx.session.undo_snapshot = remaining

        note_text = "".join(f"\nNota: {note}." for note in notes)
        if failed:
            return (
                "⚠️ No se pudo deshacer el último comando completamente "
                f"({snapshot.description}). Intenta 'deshacer' de nuevo.{note_text}"
            )
        return f"✅ Se deshizo: {snapshot.description}.{note_text}"
