"""Clase base de los comandos del bot (patrón Command + inyección de deps)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from accounting.money import parse_amount
from accounting.session_manager import CommandResult, UserSession
from accounting.undo import UndoRecorder
from database.models import Administrator, Business
from drive.drive_client import DriveClient
from sheets.layout import SheetRegion
from sheets.sheets_client import SheetsClient


@dataclass
class CommandContext:
    """Todo lo que un comando necesita para ejecutarse.

    Se construye por cada mensaje entrante (que puede traer varios
    comandos), por lo que los comandos son stateless y seguros en entornos
    con múltiples businesses simultáneos. `undo` acumula los pasos de
    deshacer de todos los comandos del mensaje.
    """

    business: Business
    administrator: Administrator
    session: UserSession
    sheets: SheetsClient
    drive: DriveClient
    undo: UndoRecorder = field(default_factory=UndoRecorder)


class Command(ABC):
    """Contrato de un comando del bot."""

    name: ClassVar[str]
    aliases: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def execute(self, ctx: CommandContext, args: list[str]) -> CommandResult:
        """Ejecuta el comando y devuelve uno o varios mensajes al usuario."""

    # ------------------------------------------------------------------
    # Helpers compartidos
    # ------------------------------------------------------------------
    @staticmethod
    def require_active_sheet(ctx: CommandContext) -> str | None:
        """Devuelve un mensaje de error si no hay planilla activa."""
        if not ctx.session.active_sheet_id:
            return (
                "⚠️ No hay una planilla activa. "
                "Usa el comando 'hoja' para seleccionar o crear una planilla."
            )
        return None

    @staticmethod
    def parse_amount(raw: str) -> float:
        """Convierte el primer argumento en monto numérico ("5.000" -> 5000)."""
        return parse_amount(raw)

    @staticmethod
    def region_full_message(region: SheetRegion) -> str:
        return (
            f"⚠️ La sección '{region.label}' de la planilla está llena "
            f"({region.capacity} filas). Crea una planilla adicional del día "
            "con 'segunda planilla' para seguir registrando."
        )
