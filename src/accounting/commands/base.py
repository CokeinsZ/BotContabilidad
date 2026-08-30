"""Clase base de los comandos del bot (patrón Command + inyección de deps)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from database.models import Administrator, Business
from drive.drive_client import DriveClient
from sheets.sheets_client import SheetsClient
from accounting.session_manager import CommandResult, UserSession


@dataclass
class CommandContext:
    """Todo lo que un comando necesita para ejecutarse.

    Se construye por cada mensaje entrante, por lo que los comandos son
    stateless y seguros en entornos con múltiples businesses simultáneos.
    """

    business: Business
    administrator: Administrator
    session: UserSession
    sheets: SheetsClient
    drive: DriveClient


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
        """Convierte el primer argumento en monto numérico."""
        return float(raw)
