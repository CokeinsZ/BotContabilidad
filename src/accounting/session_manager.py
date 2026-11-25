"""
Sesiones de usuario del bot.

Cada par (business, teléfono) tiene su propia sesión con su planilla activa,
su último mensaje deshacible y su selección pendiente.
"""
import threading
from dataclasses import dataclass, field
from typing import Callable, Union

from accounting.undo import UndoSnapshot, UndoStep

#: Respuesta de un comando: uno o varios mensajes para el usuario.
CommandResult = Union[str, list[str]]


@dataclass
class PendingSelection:
    """Una pregunta abierta al usuario que se responde con un número.

    La lógica de resolución la provee el comando que creó la selección
    (closure), por lo que el núcleo no conoce detalles de cada caso.
    """

    description: str
    menu: str                 # texto que se muestra (y se repite si la opción es inválida)
    options: int              # opciones válidas: 1..options
    resolver: Callable[[object, int], CommandResult]  # (CommandContext, opción válida) -> respuesta
    # Lo que escribió el comando que abrió el menú: si el usuario no elige
    # ninguna opción, se revierte (el comando se cancela completo).
    cancel_steps: list[UndoStep] = field(default_factory=list)
    cancel_descriptions: list[str] = field(default_factory=list)


@dataclass
class UserSession:
    """Estado de conversación de un administrador dentro de su business."""

    business_id: int
    phone_number: str
    active_sheet_id: str | None = None
    active_sheet_name: str | None = None
    undo_snapshot: UndoSnapshot | None = None
    # Cola de preguntas numeradas: se muestran y se responden de a una.
    pending_selections: list[PendingSelection] = field(default_factory=list)

    def ask(self, selection: PendingSelection) -> bool:
        """Encola una pregunta. True si es la que se debe mostrar ya (la primera)."""
        self.pending_selections.append(selection)
        return len(self.pending_selections) == 1

    def set_active_sheet(self, sheet_id: str, sheet_name: str) -> None:
        # El deshacer NO se borra al cambiar de planilla: cada paso guarda su
        # propio sheet_id, así que sigue siendo preciso, y un mensaje puede
        # traer "hoja X" junto con movimientos que deben deshacerse juntos.
        self.active_sheet_id = sheet_id
        self.active_sheet_name = sheet_name


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
