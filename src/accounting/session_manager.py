"""
Sesiones de usuario del bot.

Cada par (business, teléfono) tiene su propia sesión con su planilla activa y
su última acción deshacible. Esto elimina el estado global de la versión
anterior, donde todos los usuarios compartían una única planilla activa.
"""
import threading
from dataclasses import dataclass

from sheets.layout import SheetRegion


@dataclass
class UndoSnapshot:
    """Información necesaria para revertir la última acción del usuario."""

    sheet_id: str
    description: str
    region: SheetRegion | None = None  # si la acción agregó una fila
    cell: str | None = None            # si la acción sobrescribió una celda
    restore_value: object = ""         # valor a restaurar en `cell`


@dataclass
class UserSession:
    """Estado de conversación de un administrador dentro de su business."""

    business_id: int
    phone_number: str
    active_sheet_id: str | None = None
    active_sheet_name: str | None = None
    undo_snapshot: UndoSnapshot | None = None

    def set_active_sheet(self, sheet_id: str, sheet_name: str) -> None:
        self.active_sheet_id = sheet_id
        self.active_sheet_name = sheet_name
        # Al cambiar de planilla, la acción anterior ya no aplica.
        self.undo_snapshot = None


class SessionManager:
    """Administra las sesiones en memoria, seguro para múltiples hilos."""

    def __init__(self):
        self._sessions: dict[tuple[int, str], UserSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, business_id: int, phone_number: str) -> UserSession:
        key = (business_id, phone_number)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                session = UserSession(business_id=business_id, phone_number=phone_number)
                self._sessions[key] = session
            return session
