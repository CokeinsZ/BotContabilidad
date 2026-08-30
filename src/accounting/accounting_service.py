"""Servicio de aplicación: orquesta la ejecución de comandos del bot."""
from accounting.commands.base import CommandContext
from accounting.dispatcher import CommandDispatcher
from accounting.session_manager import CommandResult, SessionManager
from database.business_repository import BusinessRepository
from drive.drive_client import DriveClient
from sheets.sheets_client import SheetsClient


class AccountingService:
    """Fachada del núcleo de contabilidad.

    Recibe el texto de un comando junto con el teléfono del remitente,
    resuelve el business correspondiente y ejecuta el comando en su sesión.
    También gestiona las selecciones pendientes (preguntas abiertas que el
    usuario responde con un número, ej: elegir entre trabajadores similares).
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
        """Procesa un comando de texto enviado por un administrador."""
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return [
                "⚠️ Tu número no está registrado como administrador de ningún "
                f"negocio.\n\nTu identificador es: {phone_number}\n"
                "Compártelo con el proveedor del bot para darte de alta."
            ]

        if self._sheets.service is None or self._drive.service is None:
            return [
                "⚠️ El servidor aún no está autenticado con Google. "
                "Pide al administrador del sistema que abra el enlace /auth/login."
            ]

        session = self._sessions.get_or_create(
            business_context.business.id, phone_number
        )
        ctx = CommandContext(
            business=business_context.business,
            administrator=business_context.administrator,
            session=session,
            sheets=self._sheets,
            drive=self._drive,
        )

        # Una selección pendiente se responde con un número y NO pasa por el
        # dispatcher de comandos. Si llega otra cosa, la selección se cancela.
        if session.pending_selection is not None:
            if full_command.strip().isdigit():
                pending = session.pending_selection
                session.pending_selection = None
                return self._normalize(pending.resolver(ctx, full_command.strip()))
            session.pending_selection = None

        return self._dispatcher.dispatch(ctx, full_command)

    def has_pending_selection(self, phone_number: str) -> bool:
        """True si el usuario tiene una selección pendiente por responder."""
        business_context = self._businesses.find_context_by_phone(phone_number)
        if business_context is None:
            return False
        session = self._sessions.get_or_create(
            business_context.business.id, phone_number
        )
        return session.pending_selection is not None

    @staticmethod
    def _normalize(result: CommandResult) -> list[str]:
        return [result] if isinstance(result, str) else result
