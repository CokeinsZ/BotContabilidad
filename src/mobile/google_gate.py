"""¿El servidor tiene credenciales de Google? Si no, la app lo dice con un código claro."""
from drive.drive_client import DriveClient
from mobile.errors import ServiceUnavailable
from sheets.sheets_client import SheetsClient


class GoogleGate:
    def __init__(self, sheets: SheetsClient, drive: DriveClient):
        self._sheets = sheets
        self._drive = drive

    @property
    def connected(self) -> bool:
        return self._sheets.service is not None and self._drive.service is not None

    def ensure(self) -> None:
        if not self.connected:
            raise ServiceUnavailable(
                "El servidor no está conectado con Google. Avísale al proveedor del bot.",
                "GOOGLE_NO_CONECTADO",
            )
