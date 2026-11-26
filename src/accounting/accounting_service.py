"""Servicio de aplicación: orquesta la ejecución de comandos del bot."""
from accounting.commands.base import CommandContext
from accounting.dispatcher import CommandDispatcher
from accounting.session_manager import (
    WHATSAPP,
    CommandResult,
    SessionManager,
    SessionState,
    UserSession,
)
from accounting.undo import Outcome
from config.log import log_error
from database.business_repository import BusinessRepository
from drive.drive_client import DriveClient
from sheets.sheets_client import SheetsClient


NO_COMMANDS_MESSAGE = (
    "🤔 No encontré ningún comando en tu mensaje. "
    "Escribe 'instrucciones' para ver lo que puedo hacer."
)

GOOGLE_NOT_AUTHENTICATED_MESSAGE = (
    "⚠️ El servidor aún no está autenticado con Google. "
    "Pide al administrador del sistema que abra el enlace /auth/login."
)


def unregistered_message(phone_number: str) -> str:
    """Respuesta para alguien que no es administrador de ningún negocio."""
    return (
        "⚠️ Tu número no está registrado como administrador de ningún "
        f"negocio.\n\nTu identificador es: {phone_number}\n"
        "Compártelo con el proveedor del bot para darte de alta."
    )


class AccountingService:
    """Fachada del núcleo de contabilidad.

    Recibe los comandos de un mensaje junto con el teléfono del remitente,
    resuelve el business correspondiente y los ejecuta en su sesión.
    También gestiona las selecciones pendientes (preguntas abiertas que el
    usuario responde con un número, ej: elegir entre trabajadores similares).

    `channel` separa las sesiones de WhatsApp y de la app móvil (ver
    `session_manager`). Por defecto es WhatsApp.
    """

    def __init__(
        self,
        dispatcher: CommandDispatcher,
        business_repository: BusinessRepository,
        session_manager: SessionManager,
        sheets_client: SheetsClient,
        drive_client: DriveClient,
    ):
        self._dispatcher = dispatcher
        self._businesses = business_repository
        self._sessions = session_manager
        self._sheets = sheets_client
        self._drive = drive_client

    def handle_command(self, phone_number: str, full_command: str) -> list[str]:
        """Atajo para un mensaje con un único comando."""
        return self.handle_commands(phone_number, [full_command])

    def handle_commands(
        self, phone_number: str, commands: list[str], channel: str = WHATSAPP
    ) -> list[str]:
        """Ejecuta, en orden, todos los comandos de UN mensaje.

        Todo lo que modifiquen se agrupa en un único deshacer: el siguiente
        `deshacer` revierte el mensaje completo aunque traiga varios comandos.
        """
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return [unregistered_message(phone_number)]

        if not self.google_connected:
            return [GOOGLE_NOT_AUTHENTICATED_MESSAGE]

        session = self._sessions.get_or_create(business_context.business.id, phone_number, channel)
        ctx = CommandContext(
            business=business_context.business,
            administrator=business_context.administrator,
            session=session,
            sheets=self._sheets,
            drive=self._drive,
        )

        try:
            # Una selección pendiente se responde con un número y NO pasa por
            # el dispatcher. Si llega cualquier otra cosa, el usuario no eligió
            # ninguna opción: los comandos que preguntaron se cancelan completos.
            responses: list[str] = []
            if session.pending_selections:
                answer = commands[0].strip() if len(commands) == 1 else ""
                if answer.isdigit():
                    return self._answer_selection(ctx, int(answer))
                responses.extend(self._cancel_pending_selections(ctx))

            if not commands:
                return [*responses, NO_COMMANDS_MESSAGE]
            for command in commands:
                responses.extend(self._dispatcher.dispatch(ctx, command))
            if ctx.undo.has_steps:
                session.undo_snapshot = ctx.undo.to_snapshot()
            return responses
        except Exception as error:
            log_error(
                "procesando comandos en AccountingService",
                error,
                f"phone={phone_number} business_id={business_context.business.id} "
                f"commands={commands!r} sheet_id={session.active_sheet_id} "
                f"sheet_name={session.active_sheet_name!r}",
            )
            # Lo que alcanzó a escribirse antes del error sigue siendo deshacible.
            if ctx.undo.has_steps:
                session.undo_snapshot = ctx.undo.to_snapshot()
            return [
                "⚠️ Ocurrió un error interno al procesar el comando. "
                "Revisa los logs del servidor para el detalle."
            ]

    def _answer_selection(self, ctx: CommandContext, option: int) -> list[str]:
        session = ctx.session
        pending = session.pending_selections[0]
        if not 1 <= option <= pending.options:
            return [f"⚠️ Opción inválida: {option}.", pending.menu]
        session.pending_selections.pop(0)
        result = self._normalize(pending.resolver(ctx, option))
        # La respuesta completa el mensaje que abrió el menú: sus pasos se
        # suman al deshacer de ese mensaje.
        if ctx.undo.has_steps:
            session.undo_snapshot = ctx.undo.merge_into(session.undo_snapshot)
        if session.pending_selections:
            result = [*result, session.pending_selections[0].menu]
        return result

    def _cancel_pending_selections(self, ctx: CommandContext) -> list[str]:
        """Revierte lo que escribieron los comandos cuyo menú no se respondió."""
        session = ctx.session
        cancelled = list(session.pending_selections)
        session.pending_selections.clear()

        snapshot = session.undo_snapshot
        failed = False
        for selection in cancelled:
            undone = []
            for step in reversed(selection.cancel_steps):
                try:
                    outcome = step.undo(self._sheets).outcome
                except Exception as error:
                    log_error("cancelando comando con menú sin responder", error,
                              f"business_id={ctx.business.id} command={selection.description!r}")
                    outcome = Outcome.FAILED
                if outcome is Outcome.FAILED:
                    failed = True
                else:
                    undone.append(step)
            if snapshot is not None:
                complete = len(undone) == len(selection.cancel_steps)
                snapshot = snapshot.without(undone, selection.cancel_descriptions if complete else [])
        session.undo_snapshot = snapshot

        commands = "; ".join(f"'{s.description}'" for s in cancelled)
        if failed:
            return [
                f"⚠️ No escogiste ninguna opción del menú, así que se canceló {commands}, "
                "pero no se pudo borrar de la planilla. Usa 'deshacer' para quitarlo."
            ]
        return [
            f"⚠️ No escogiste ninguna opción del menú, así que se canceló {commands} "
            "y se borró de la planilla."
        ]

    def has_pending_selection(self, phone_number: str, channel: str = WHATSAPP) -> bool:
        """True si el usuario tiene una selección pendiente por responder."""
        session = self._session(phone_number, channel)
        return session is not None and bool(session.pending_selections)

    # ------------------------------------------------------------------
    # Operaciones para clientes que no son WhatsApp (app móvil)
    # ------------------------------------------------------------------
    @property
    def google_connected(self) -> bool:
        """True si el servidor tiene credenciales válidas de Google."""
        return self._sheets.service is not None and self._drive.service is not None

    def select_sheet(self, phone_number: str, channel: str, sheet_id: str, sheet_name: str) -> bool:
        """Fija la planilla activa sin pasar por el comando 'hoja'.

        La app abre una planilla concreta (ya verificada como del negocio) y
        todo lo que se escribe en su chat va a esa planilla. Devuelve False si
        el teléfono no es de un administrador activo.
        """
        session = self._session(phone_number, channel)
        if session is None:
            return False
        session.set_active_sheet(sheet_id, sheet_name)
        return True

    def session_state(self, phone_number: str, channel: str) -> SessionState | None:
        """Planilla activa, qué revertiría 'deshacer' y la pregunta pendiente."""
        session = self._session(phone_number, channel)
        return session.state() if session is not None else None

    def cancel_pending(self, phone_number: str, channel: str) -> list[str]:
        """Cancela las preguntas sin responder, igual que un mensaje cualquiera.

        Revierte lo que escribieron los comandos que preguntaron. Devuelve []
        si no había ninguna pregunta pendiente.
        """
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return []
        session = self._sessions.get_or_create(business_context.business.id, phone_number, channel)
        if not session.pending_selections:
            return []
        ctx = CommandContext(
            business=business_context.business,
            administrator=business_context.administrator,
            session=session,
            sheets=self._sheets,
            drive=self._drive,
        )
        return self._cancel_pending_selections(ctx)

    def run_detached(self, phone_number: str, commands: list[str]) -> tuple[list[str], SessionState | None]:
        """Ejecuta comandos en una sesión temporal que no se guarda.

        La app crea y abre planillas así: no toca la conversación del chat
        (no cancela una pregunta pendiente ni reemplaza el deshacer) y la
        planilla activa que devuelve es la que dejó ESTE comando, no una de
        antes. Devuelve (respuestas, estado de la sesión temporal).
        """
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return [unregistered_message(phone_number)], None
        if not self.google_connected:
            return [GOOGLE_NOT_AUTHENTICATED_MESSAGE], None

        session = UserSession(
            business_id=business_context.business.id, phone_number=phone_number, channel="detached"
        )
        ctx = CommandContext(
            business=business_context.business,
            administrator=business_context.administrator,
            session=session,
            sheets=self._sheets,
            drive=self._drive,
        )
        responses: list[str] = []
        for command in commands:
            responses.extend(self._dispatcher.dispatch(ctx, command))
        return responses, session.state()

    def _session(self, phone_number: str, channel: str):
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return None
        return self._sessions.get_or_create(business_context.business.id, phone_number, channel)

    @staticmethod
    def _normalize(result: CommandResult) -> list[str]:
        return [result] if isinstance(result, str) else result
