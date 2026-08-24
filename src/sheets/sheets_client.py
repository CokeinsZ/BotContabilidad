"""
Cliente de bajo nivel para la API de Google Sheets.

Optimización clave respecto a la versión anterior: todas las escrituras y
lecturas múltiples usan `values.batchUpdate` / `values.batchGet`, reduciendo
cada operación de negocio a un máximo de 2 llamadas HTTP a la API (antes eran
3 por cada comando).
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth.google_auth_manager import GoogleAuthManager
from sheets.layout import PlanillaLayout, SheetRegion


class SheetsClient:
    """Operaciones sobre planillas, agnóstico del business (stateless)."""

    def __init__(self, auth_manager: GoogleAuthManager, layout: PlanillaLayout | None = None):
        self._auth_manager = auth_manager
        self.layout = layout or PlanillaLayout()
        self._service = None
        self._credentials_used = None

    @property
    def service(self):
        """Construye el servicio de la API de forma perezosa.

        No exige credenciales en el arranque del servidor: solo cuando se
        usa por primera vez. Devuelve None si aún no hay autenticación.
        Se reconstruye automáticamente si las credenciales cambian (re-login).
        """
        credentials = self._auth_manager.get_credentials()
        if credentials is None:
            return None
        if self._service is None or credentials is not self._credentials_used:
            self._service = build("sheets", "v4", credentials=credentials)
            self._credentials_used = credentials
        return self._service

    # ------------------------------------------------------------------
    # Operaciones por lotes (batch)
    # ------------------------------------------------------------------
    def get_values(self, sheet_id: str, ranges: list[str]) -> dict[str, list[list]]:
        """Lee varios rangos en UNA sola llamada (`values.batchGet`)."""
        try:
            response = (
                self.service.spreadsheets()
                .values()
                .batchGet(spreadsheetId=sheet_id, ranges=ranges)
                .execute()
            )
            result: dict[str, list[list]] = {}
            for value_range in response.get("valueRanges", []):
                result[value_range.get("range", "").split("!")[-1]] = value_range.get(
                    "values", [[]]
                )
            return result
        except HttpError as error:
            print(f"Error leyendo rangos {ranges} de {sheet_id}: {error}")
            return {}

    def set_values(self, sheet_id: str, updates: dict[str, list[list]]) -> bool:
        """Escribe varios rangos en UNA sola llamada (`values.batchUpdate`)."""
        try:
            body = {
                "valueInputOption": "RAW",
                "data": [{"range": key, "values": values} for key, values in updates.items()],
            }
            result = (
                self.service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=sheet_id, body=body)
                .execute()
            )
            return bool(result.get("totalUpdatedCells"))
        except HttpError as error:
            print(f"Error escribiendo rangos de {sheet_id}: {error}")
            return False

    def get_value(self, sheet_id: str, range_a1: str) -> str | None:
        """Lee una única celda."""
        values = self.get_values(sheet_id, [range_a1]).get(range_a1, [[]])
        if values and values[0]:
            return values[0][0]
        return None

    # ------------------------------------------------------------------
    # Regiones dinámicas (gastos, trabajadores, retiros, ...)
    # ------------------------------------------------------------------
    def append_to_region(self, sheet_id: str, region: SheetRegion, values: list) -> bool:
        """Agrega una fila a una región y avanza su contador. 2 llamadas API."""
        counter = self.get_value(sheet_id, region.counter_cell)
        if counter is None:
            return False
        try:
            row = int(counter)
        except (TypeError, ValueError):
            return False

        return self.set_values(
            sheet_id,
            {
                region.row_range(row): [values],
                region.counter_cell: [[row + 1]],
            },
        )

    def undo_last_entry(self, sheet_id: str, region: SheetRegion) -> bool:
        """Elimina la última fila de una región y retrocede su contador."""
        counter = self.get_value(sheet_id, region.counter_cell)
        if counter is None:
            return False
        try:
            target_row = int(counter) - 1
        except (TypeError, ValueError):
            return False
        if target_row < region.min_row:
            return False

        try:
            self.service.spreadsheets().values().batchClear(
                spreadsheetId=sheet_id,
                body={"ranges": [region.row_range(target_row)]},
            ).execute()
        except HttpError as error:
            print(f"Error limpiando fila {target_row} de {sheet_id}: {error}")
            return False

        return self.set_values(sheet_id, {region.counter_cell: [[target_row]]})

    # ------------------------------------------------------------------
    # Resumen diario
    # ------------------------------------------------------------------
    def get_daily_totals(
        self, sheet_id: str
    ) -> tuple[str, str, str, str, str] | None:
        """Devuelve (gastos, efectivo, ventas, saldo_previo, saldo_total)."""
        values = self.get_values(sheet_id, [self.layout.totals_range]).get(
            self.layout.totals_range, [[]]
        )

        def value_at(index: int, default: str = "0") -> str:
            if index < len(values) and values[index]:
                return values[index][0]
            return default

        return (
            value_at(0),  # B38 gastos totales
            value_at(1),  # B39 efectivo del día
            value_at(2),  # B40 ventas totales
            value_at(4),  # B42 saldo previo
            value_at(8),  # B46 saldo total
        )
