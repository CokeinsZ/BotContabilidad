"""
Sesiones de usuario del bot.

Cada (business, teléfono, canal) tiene su propia sesión con su planilla
activa, su último mensaje deshacible y su selección pendiente. El canal
separa WhatsApp de la app móvil: un `deshacer` en WhatsApp nunca revierte lo
que se hizo en la app (y viceversa), y la planilla activa de uno no cambia la
del otro.
"""
import threading
from dataclasses import dataclass, field
from typing import Callable, Union

from accounting.undo import UndoSnapshot, UndoStep

#: Respuesta de un comando: uno o varios mensajes para el usuario.
CommandResult = Union[str, list[str]]

#: Canales por los que llega un administrador.
WHATSAPP = "whatsapp"
APP = "app"


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
    # Para clientes que dibujan la pregunta como botones (app móvil): la
    # pregunta sin las opciones y la etiqueta de cada opción (1..options).
    prompt: str = ""
    option_labels: list[str] = field(default_factory=list)
    # Planilla activa cuando se hizo la pregunta.
    sheet_id: str | None = None
    sheet_name: str | None = None


@dataclass(frozen=True)
class SessionState:
    """Foto de la sesión para clientes que no son WhatsApp (solo lectura)."""

    active_sheet_id: str | None
    active_sheet_name: str | None
    undo_description: str | None          # qué revertiría 'deshacer' (None = nada)
    selection: PendingSelection | None    # pregunta que hay que responder ya


@dataclass
class UserSession:
    """Estado de conversación de un administrador dentro de su business."""

    business_id: int
    phone_number: str
    channel: str = WHATSAPP
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

    def state(self) -> SessionState:
        snapshot = self.undo_snapshot
        return SessionState(
            active_sheet_id=self.active_sheet_id,
            active_sheet_name=self.active_sheet_name,
            undo_description=snapshot.description if snapshot and snapshot.steps else None,
            selection=self.pending_selections[0] if self.pending_selections else None,
        )


class SessionManager:
    """Administra las sesiones en memoria, seguro para múltiples hilos."""

    def __init__(self):
        self._sessions: dict[tuple[int, str, str], UserSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, business_id: int, phone_number: str, channel: str = WHATSAPP) -> UserSession:
        key = (business_id, phone_number, channel)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                session = UserSession(business_id=business_id, phone_number=phone_number, channel=channel)
                self._sessions[key] = session
            return session
