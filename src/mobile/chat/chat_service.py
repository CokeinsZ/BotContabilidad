"""Chat de una planilla en la app: lo que el administrador envía y lo que el bot responde.

El historial NO se guarda en el servidor: la app lo guarda en el SQLite del
teléfono. Aquí solo se ejecutan los comandos y se devuelven las respuestas.

- Cada mensaje trae un `client_id`. Si la app lo reenvía (mala señal), se
  devuelve la misma respuesta sin volver a registrar nada. Esas respuestas
  se recuerdan en memoria una hora; no se guardan en disco.
- Los mensajes de un administrador se procesan de a uno y en orden.
- Antes de ejecutar, la planilla abierta en la app queda como planilla
  activa de la sesión del canal "app" (separada de la de WhatsApp).
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from accounting.accounting_service import AccountingService
from accounting.commands.cash_commands import WithdrawalCommand
from accounting.commands.employee_commands import NominaCommand, WorkerLoanCommand
from accounting.dispatcher import CommandDispatcher
from accounting.session_manager import APP, SessionState
from config.clock import now
from database.models import BusinessContext
from mobile.cache import TtlCache
from mobile.chat.command_builder import CommandBuilder
from mobile.chat.message_kinds import SELECCION, classify
from mobile.errors import Conflict, Unprocessable
from mobile.google_gate import GoogleGate
from mobile.locks import KeyedLocks
from mobile.ownership import Ownership, PlanillaRef

#: Comandos que pueden crear o cambiar archivos de trabajadores.
_WORKER_COMMANDS = (WorkerLoanCommand, NominaCommand, WithdrawalCommand)


@dataclass(frozen=True)
class BotReply:
    kind: str
    text: str


@dataclass(frozen=True)
class ChatResult:
    replies: list[BotReply]
    state: SessionState | None
    processed_at: datetime
    client_id: str | None = None
    commands: list[str] = field(default_factory=list)
    used_ai: bool = False


def to_replies(responses: list[str], state: SessionState | None) -> list[BotReply]:
    """Clasifica las respuestas. El menú numerado se marca como pregunta."""
    selection = state.selection if state else None
    replies = []
    for response in responses:
        if not response:
            continue
        if selection is not None and response == selection.menu:
            replies.append(BotReply(SELECCION, selection.prompt or classify(response)[1]))
        else:
            replies.append(BotReply(*classify(response)))
    return replies


class ChatService:
    def __init__(
        self,
        accounting: AccountingService,
        dispatcher: CommandDispatcher,
        builder: CommandBuilder,
        ownership: Ownership,
        google: GoogleGate,
        locks: KeyedLocks,
        listings: TtlCache,
        results: TtlCache | None = None,
    ):
        self._accounting = accounting
        self._dispatcher = dispatcher
        self._builder = builder
        self._ownership = ownership
        self._google = google
        self._locks = locks
        self._listings = listings
        self._results = results or TtlCache(ttl_seconds=3600, max_items=2000)

    async def send(
        self, ctx: BusinessContext, sheet_id: str, client_id: str, command_id: str | None, text: str
    ) -> ChatResult:
        sheet = await self._sheet(ctx, sheet_id)
        key = (ctx.administrator.id, client_id)
        if (cached := self._results.get(key)) is not None:
            return cached

        async with self._admin_lock(ctx):
            if (cached := self._results.get(key)) is not None:
                return cached     # el reintento llegó mientras se procesaba el original

            built = await self._builder.build(command_id, text)
            phone = ctx.administrator.phone_number

            def run():
                if not built.commands and built.rejected:
                    return [], self._accounting.session_state(phone, APP)
                self._accounting.select_sheet(phone, APP, sheet.id, sheet.name)
                responses = self._accounting.handle_commands(phone, built.commands, APP)
                return responses, self._accounting.session_state(phone, APP)

            responses, state = await asyncio.to_thread(run)
            if built.rejected:
                rejected = ", ".join(f"'{command}'" for command in built.rejected)
                responses = [
                    *responses,
                    f"⚠️ Para cambiar de planilla usa la pantalla Planillas. No se ejecutó: {rejected}.",
                ]
            if self._touches_workers(built.commands):
                self._listings.invalidate(lambda k: k[:2] == ("trabajadores", ctx.business.id))
            self._invalidate_planilla_reads(ctx, sheet)

            result = ChatResult(
                replies=to_replies(responses, state),
                state=state,
                processed_at=now(),
                client_id=client_id,
                commands=list(built.commands),
                used_ai=built.used_ai,
            )
            self._results.set(key, result)
            return result

    async def answer(self, ctx: BusinessContext, sheet_id: str, option: int) -> ChatResult:
        """Responde la pregunta pendiente (p. ej. en cuál archivo guardar el préstamo)."""
        await self._sheet(ctx, sheet_id)
        phone = ctx.administrator.phone_number
        async with self._admin_lock(ctx):
            state = await asyncio.to_thread(self._accounting.session_state, phone, APP)
            selection = state.selection if state else None
            if selection is None:
                raise Conflict("No hay ninguna pregunta pendiente.", "SIN_PREGUNTA")
            if not 1 <= option <= selection.options:
                raise Unprocessable(
                    f"Opción inválida: elige entre 1 y {selection.options}.", "OPCION_INVALIDA"
                )

            def run():
                responses = self._accounting.handle_commands(phone, [str(option)], APP)
                return responses, self._accounting.session_state(phone, APP)

            responses, new_state = await asyncio.to_thread(run)
            self._listings.invalidate(lambda k: k[:2] == ("trabajadores", ctx.business.id))
            return ChatResult(to_replies(responses, new_state), new_state, now())

    async def cancel(self, ctx: BusinessContext, sheet_id: str) -> ChatResult:
        """Cancela la pregunta pendiente: el comando que preguntó se borra de la planilla."""
        sheet = await self._sheet(ctx, sheet_id)
        phone = ctx.administrator.phone_number
        async with self._admin_lock(ctx):
            def run():
                responses = self._accounting.cancel_pending(phone, APP)
                return responses, self._accounting.session_state(phone, APP)

            responses, state = await asyncio.to_thread(run)
            if not responses:
                raise Conflict("No hay ninguna pregunta pendiente.", "SIN_PREGUNTA")
            self._invalidate_planilla_reads(ctx, sheet)
            return ChatResult(to_replies(responses, state), state, now())

    async def state(self, ctx: BusinessContext, sheet_id: str) -> SessionState | None:
        """Pregunta pendiente y qué revertiría 'deshacer' (al abrir el chat)."""
        await self._sheet(ctx, sheet_id)
        return await asyncio.to_thread(
            self._accounting.session_state, ctx.administrator.phone_number, APP
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    async def _sheet(self, ctx: BusinessContext, sheet_id: str) -> PlanillaRef:
        self._google.ensure()
        return await asyncio.to_thread(self._ownership.planilla, ctx.business, sheet_id)

    def _admin_lock(self, ctx: BusinessContext):
        return self._locks.get(("admin", ctx.administrator.id))

    def _touches_workers(self, commands: list[str]) -> bool:
        return any(isinstance(self._dispatcher.resolve(c), _WORKER_COMMANDS) for c in commands)

    def _invalidate_planilla_reads(self, ctx: BusinessContext, sheet: PlanillaRef) -> None:
        """Los totales de la planilla y la tarjeta de hoy cambian con cada movimiento."""
        self._listings.invalidate(
            lambda k: k[:2] == ("hoy", ctx.business.id) or k == ("totales", sheet.id)
        )
