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

    # ------------------------------------------------------------------
    # Operaciones estructurales de hojas (batchUpdate)
    # ------------------------------------------------------------------
    def get_sheet_id_by_name(self, spreadsheet_id: str, sheet_name: str) -> int | None:
        """Devuelve el sheetId (numérico) de una hoja por su nombre."""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title))"
            ).execute()
            for sheet in spreadsheet.get("sheets", []):
                if sheet["properties"]["title"] == sheet_name:
                    return sheet["properties"]["sheetId"]
            return None
        except HttpError as error:
            print(f"Error obteniendo sheetId de '{sheet_name}': {error}")
            return None

    def duplicate_sheet(self, spreadsheet_id: str, source_sheet_id: int, new_name: str) -> int | None:
        """Duplica una hoja dentro del mismo spreadsheet y la renombra.

        Devuelve el sheetId de la nueva hoja.
        """
        try:
            request = {
                "duplicateSheet": {
                    "sourceSheetId": source_sheet_id,
                    "newSheetName": new_name,
                }
            }
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [request]}
            ).execute()
            new_sheet_id = response["replies"][0]["duplicateSheet"]["properties"]["sheetId"]
            return new_sheet_id
        except HttpError as error:
            print(f"Error duplicando hoja {source_sheet_id} a '{new_name}': {error}")
            return None

    def delete_rows(self, spreadsheet_id: str, sheet_id: int, start_row: int, end_row: int) -> bool:
        """Borra filas [start_row, end_row) (1-indexed, end exclusivo) de una hoja.

        Nota: la API usa índices 0-based, así que restamos 1.
        """
        try:
            request = {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_row - 1,
                        "endIndex": end_row - 1,
                    }
                }
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [request]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error borrando filas {start_row}-{end_row} de hoja {sheet_id}: {error}")
            return False

    def clear_range(self, spreadsheet_id: str, range_a1: str, fill_value: str | int = "") -> bool:
        """Limpia un rango escribiendo un valor (vacío o 0)."""
        try:
            # Primero obtener dimensiones del rango para saber cuántas celdas escribir
            values = self.get_values(spreadsheet_id, [range_a1]).get(range_a1, [[]])
            if not values:
                return True
            rows = len(values)
            cols = max(len(row) for row in values) if values else 1
            fill_values = [[fill_value] * cols for _ in range(rows)]
            return self.set_values(spreadsheet_id, {range_a1: fill_values})
        except HttpError as error:
            print(f"Error limpiando rango {range_a1}: {error}")
            return False

    def clear_range_a1(self, spreadsheet_id: str, range_a1: str, fill_value: str | int = "") -> bool:
        """Limpia un rango A1 específico escribiendo fill_value.

        Soporta notación con nombre de hoja: "'Hoja 1'!A1:B2" o "A1:B2".
        """
        try:
            # Separar nombre de hoja si existe: "'Hoja'!A1:B2" -> sheet_part, cell_range
            if "!" in range_a1:
                _, cell_range = range_a1.split("!", 1)
            else:
                cell_range = range_a1

            # Parsear el rango de celdas para saber dimensiones
            if ":" not in cell_range:
                # Celda simple
                fill_values = [[fill_value]]
            else:
                start, end = cell_range.split(":")
                # Parsear coordenadas (solo letras + números, sin nombre de hoja)
                def parse_cell(cell):
                    col = ""
                    row = ""
                    for ch in cell:
                        if ch.isalpha():
                            col += ch
                        else:
                            row += ch
                    return col, int(row)
                start_col, start_row = parse_cell(start)
                end_col, end_row = parse_cell(end)
                rows = end_row - start_row + 1
                # Contar columnas
                def col_to_num(col):
                    num = 0
                    for ch in col:
                        num = num * 26 + (ord(ch.upper()) - ord('A') + 1)
                    return num
                cols = col_to_num(end_col) - col_to_num(start_col) + 1
                fill_values = [[fill_value] * cols for _ in range(rows)]

            # Usar el range_a1 original (con nombre de hoja si lo tenía) para la escritura
            return self.set_values(spreadsheet_id, {range_a1: fill_values})
        except HttpError as error:
            print(f"Error limpiando rango {range_a1}: {error}")
            return False
        except Exception as error:
            print(f"Error parseando rango {range_a1}: {error}")
            return False

    def reset_counter(self, spreadsheet_id: str, counter_cell: str, value: int) -> bool:
        """Reinicia un contador a un valor específico."""
        return self.set_values(spreadsheet_id, {counter_cell: [[value]]})

    # ------------------------------------------------------------------
    # Operaciones específicas para nómina
    # ------------------------------------------------------------------
    def get_worker_loan_sum(self, spreadsheet_id: str) -> str | None:
        """Obtiene la suma de préstamos (B30) del archivo del trabajador."""
        return self.get_value(spreadsheet_id, "B30")
