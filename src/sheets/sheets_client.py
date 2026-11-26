"""
Cliente de bajo nivel para la API de Google Sheets.

Principios:
- Las escrituras y lecturas múltiples usan `values.batchUpdate` /
  `values.batchGet` (una llamada HTTP por operación).
- Las lecturas de datos usan `UNFORMATTED_VALUE` (números como números). Leer
  el valor formateado ("$1.234.567") y escribirlo de vuelta con RAW dejaba
  texto donde debía haber un número.
- Toda operación leer-contador → escribir se hace bajo un lock por
  spreadsheet: dos administradores escribiendo a la vez en la misma planilla
  ya no pueden pisarse la misma fila (el bot corre en un único proceso).
"""
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google_api import execute

from auth.google_auth_manager import GoogleAuthManager
from config.log import log_error, log_warning
from sheets.a1 import cell_at, range_start
from sheets.layout import PlanillaLayout, SheetRegion

UNFORMATTED = "UNFORMATTED_VALUE"
FORMULA = "FORMULA"


class RegionFullError(Exception):
    """La región ya ocupó todas sus filas válidas."""

    def __init__(self, region: SheetRegion):
        super().__init__(f"Región '{region.label}' llena ({region.capacity} filas)")
        self.region = region


class RemoveResult(Enum):
    REMOVED = "removed"
    NOT_FOUND = "not_found"   # la fila ya no existe (borrada a mano u otro deshacer)
    ERROR = "error"


class RestoreResult(Enum):
    RESTORED = "restored"
    CHANGED = "changed"       # alguien modificó la celda después: no se pisa
    ERROR = "error"


@dataclass(frozen=True)
class DailyTotals:
    total_expenses: object
    day_cash: object
    total_sales: object
    previous_balance: object
    total_balance: object


@dataclass(frozen=True)
class PlanillaOverview:
    """Totales de la planilla y el contador de cada sección (atributo del layout -> valor)."""

    totals: DailyTotals
    counters: dict[str, object]


def same_value(left, right) -> bool:
    """Compara valores de celda tolerando 5000 vs 5000.0 y None vs ''."""
    left = "" if left is None else left
    right = "" if right is None else right
    numeric = (int, float)
    if isinstance(left, numeric) and isinstance(right, numeric) and not isinstance(left, bool):
        return float(left) == float(right)
    return str(left).strip() == str(right).strip()


def _is_formula(value) -> bool:
    return isinstance(value, str) and value.startswith("=")


def _pad(row: list, width: int) -> list:
    return list(row) + [""] * (width - len(row))


class SheetsClient:
    """Operaciones sobre planillas, agnóstico del business (stateless)."""

    def __init__(self, auth_manager: GoogleAuthManager | None, layout: PlanillaLayout | None = None):
        self._auth_manager = auth_manager
        self.layout = layout or PlanillaLayout()
        self._service = None
        self._credentials_used = None
        self._locks: dict[str, threading.RLock] = {}
        self._locks_guard = threading.Lock()

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
    # Concurrencia
    # ------------------------------------------------------------------
    @contextmanager
    def lock(self, spreadsheet_id: str):
        """Serializa las operaciones compuestas sobre un mismo spreadsheet."""
        with self._locks_guard:
            lock = self._locks.setdefault(spreadsheet_id, threading.RLock())
        with lock:
            yield

    # ------------------------------------------------------------------
    # Lecturas y escrituras por lotes
    # ------------------------------------------------------------------
    def get_values(
        self, sheet_id: str, ranges: list[str], render: str = UNFORMATTED
    ) -> dict[str, list[list]] | None:
        """Lee varios rangos en UNA sola llamada (`values.batchGet`).

        Las claves del resultado son los rangos EXACTOS solicitados (la API
        devuelve los valueRanges en el mismo orden de la petición). Devuelve
        None si la llamada falla (distinto de "celdas vacías").
        """
        try:
            response = execute(
                self.service.spreadsheets()
                .values()
                .batchGet(spreadsheetId=sheet_id, ranges=ranges, valueRenderOption=render)
            )
            value_ranges = response.get("valueRanges", [])
            result: dict[str, list[list]] = {}
            for index, requested in enumerate(ranges):
                values = value_ranges[index].get("values", []) if index < len(value_ranges) else []
                result[requested] = values
            return result
        except HttpError as error:
            log_error("leyendo rangos de Sheets", error, f"sheet_id={sheet_id} ranges={ranges}")
            return None
        except Exception as error:
            log_error("leyendo rangos de Sheets (inesperado)", error, f"sheet_id={sheet_id} ranges={ranges}")
            return None

    def get_value(self, sheet_id: str, range_a1: str, render: str = UNFORMATTED):
        """Lee una única celda (None si está vacía o si la lectura falla)."""
        values = (self.get_values(sheet_id, [range_a1], render) or {}).get(range_a1, [])
        if values and values[0]:
            return values[0][0]
        return None

    def set_values(
        self, sheet_id: str, updates: dict[str, list[list]], input_option: str = "RAW"
    ) -> bool:
        """Escribe varios rangos en UNA sola llamada (`values.batchUpdate`)."""
        try:
            body = {
                "valueInputOption": input_option,
                "data": [{"range": key, "values": values} for key, values in updates.items()],
            }
            result = execute(
                self.service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=sheet_id, body=body)
            )
            if not result.get("totalUpdatedCells"):
                log_warning(
                    "escribiendo rangos en Sheets (0 celdas actualizadas)",
                    f"sheet_id={sheet_id} ranges={list(updates)} updates={updates} response={result}",
                )
                return False
            return True
        except HttpError as error:
            log_error("escribiendo rangos en Sheets", error, f"sheet_id={sheet_id} ranges={list(updates)} updates={updates}")
            return False
        except Exception as error:
            log_error("escribiendo rangos en Sheets (inesperado)", error, f"sheet_id={sheet_id} ranges={list(updates)} updates={updates}")
            return False

    def write_preserving_formulas(self, sheet_id: str, updates: dict[str, list[list]]) -> bool:
        """Escribe valores leídos con render FORMULA conservando las fórmulas.

        Todo se escribe RAW (los textos como "24-11-2026" no se convierten en
        fechas) y luego, solo si hay celdas con fórmula, esas celdas se
        reescriben con USER_ENTERED para que vuelvan a ser fórmulas.
        """
        formula_updates: dict[str, list[list]] = {}
        for range_a1, rows in updates.items():
            prefix, first_column, first_row = range_start(range_a1)
            for row_offset, row in enumerate(rows):
                for column_offset, value in enumerate(row):
                    if _is_formula(value):
                        cell = cell_at(prefix, first_column + column_offset, first_row + row_offset)
                        formula_updates[cell] = [[value]]
        if not self.set_values(sheet_id, updates):
            return False
        if formula_updates:
            return self.set_values(sheet_id, formula_updates, input_option="USER_ENTERED")
        return True

    # ------------------------------------------------------------------
    # Regiones dinámicas (gastos, trabajadores, retiros, ...)
    # ------------------------------------------------------------------
    def _read_counter(self, sheet_id: str, region: SheetRegion) -> int | None:
        counter = self.get_value(sheet_id, region.counter_cell)
        try:
            row = int(counter)
        except (TypeError, ValueError):
            log_warning(
                "contador de región vacío o no numérico",
                f"sheet_id={sheet_id} counter_cell={region.counter_cell} counter={counter!r} "
                f"region={region.label!r} -> revisa que la planilla tenga el layout esperado",
            )
            return None
        if row < region.min_row:
            log_warning(
                "contador de región por debajo de la fila mínima",
                f"sheet_id={sheet_id} counter_cell={region.counter_cell} counter={row} "
                f"min_row={region.min_row} region={region.label!r}",
            )
            return None
        return row

    def append_to_region(self, sheet_id: str, region: SheetRegion, values: list) -> int | None:
        """Agrega una fila a una región y avanza su contador (2 llamadas API).

        Devuelve la fila escrita, o None si falla.

        Raises:
            RegionFullError: si la región ya usó todas sus filas.
        """
        with self.lock(sheet_id):
            row = self._read_counter(sheet_id, region)
            if row is None:
                return None
            if row > region.max_row:
                log_warning(
                    "región llena",
                    f"sheet_id={sheet_id} region={region.label!r} counter={row} max_row={region.max_row}",
                )
                raise RegionFullError(region)
            ok = self.set_values(
                sheet_id,
                {region.row_range(row): [list(values)], region.counter_cell: [[row + 1]]},
            )
            return row if ok else None

    def remove_region_entry(
        self, sheet_id: str, region: SheetRegion, row: int, values: list
    ) -> RemoveResult:
        """Elimina UNA entrada concreta de una región y compacta las de abajo.

        A diferencia del antiguo "borrar la última fila", se busca la fila que
        escribió este comando (verificando su contenido), así un deshacer de
        un administrador no borra lo que escribió otro. Las filas posteriores
        suben una posición y el contador retrocede uno.
        """
        with self.lock(sheet_id):
            counter = self._read_counter(sheet_id, region)
            if counter is None:
                return RemoveResult.ERROR
            last_row = min(counter, region.max_row + 1) - 1
            if last_row < region.min_row:
                return RemoveResult.NOT_FOUND

            block_range = region.block_range(region.min_row, last_row)
            block = (self.get_values(sheet_id, [block_range], FORMULA) or {}).get(block_range)
            if block is None:
                return RemoveResult.ERROR
            rows = [_pad(r, region.width) for r in block]
            rows += [_pad([], region.width)] * (last_row - region.min_row + 1 - len(rows))

            def matches(index: int) -> bool:
                current = rows[index]
                return all(same_value(current[i], v) for i, v in enumerate(values))

            preferred = row - region.min_row
            if 0 <= preferred < len(rows) and matches(preferred):
                target = preferred
            else:
                target = next((i for i in range(len(rows) - 1, -1, -1) if matches(i)), None)
            if target is None:
                log_warning(
                    "deshacer: la fila ya no existe en la región",
                    f"sheet_id={sheet_id} region={region.label!r} row={row} values={values}",
                )
                return RemoveResult.NOT_FOUND

            shifted = rows[target + 1:] + [region.blank_row]
            first_row = region.min_row + target
            ok = self.write_preserving_formulas(
                sheet_id,
                {
                    region.block_range(first_row, last_row): shifted,
                    region.counter_cell: [[last_row]],
                },
            )
            return RemoveResult.REMOVED if ok else RemoveResult.ERROR

    def restore_cell(self, sheet_id: str, cell: str, expected_current, restore_value) -> RestoreResult:
        """Restaura una celda solo si aún tiene el valor que escribió el bot."""
        with self.lock(sheet_id):
            values = self.get_values(sheet_id, [cell], FORMULA)
            if values is None:
                return RestoreResult.ERROR
            current = values.get(cell, [])
            current_value = current[0][0] if current and current[0] else ""
            if not same_value(current_value, expected_current):
                log_warning(
                    "deshacer: la celda cambió después del comando, no se restaura",
                    f"sheet_id={sheet_id} cell={cell} current={current_value!r} expected={expected_current!r}",
                )
                return RestoreResult.CHANGED
            ok = self.write_preserving_formulas(sheet_id, {cell: [[restore_value]]})
            return RestoreResult.RESTORED if ok else RestoreResult.ERROR

    # ------------------------------------------------------------------
    # Resumen diario
    # ------------------------------------------------------------------
    def _totals_cells(self) -> list[str]:
        layout = self.layout
        return [
            layout.total_expenses_cell,
            layout.day_cash_cell,
            layout.total_sales_cell,
            layout.generated_cash_cell,
            layout.total_cash_cell,
        ]

    def get_daily_totals(self, sheet_id: str) -> DailyTotals | None:
        """Lee los totales del bloque "MANEJO DEL EFECTIVO" por celda nombrada."""
        overview = self.get_planilla_overview(sheet_id)
        return overview.totals if overview is not None else None

    def get_planilla_overview(self, sheet_id: str) -> "PlanillaOverview | None":
        """Totales y contadores de todas las secciones en UNA sola lectura."""
        cells = self._totals_cells()
        regions = self.layout.daily_regions
        counters = [region.counter_cell for _attr, region in regions]
        values = self.get_values(sheet_id, cells + counters)
        if values is None:
            return None

        def value_of(cell: str, default):
            rows = values.get(cell, [])
            return rows[0][0] if rows and rows[0] else default

        return PlanillaOverview(
            totals=DailyTotals(*(value_of(cell, 0) for cell in cells)),
            counters={attr: value_of(region.counter_cell, None) for attr, region in regions},
        )

    # ------------------------------------------------------------------
    # Operaciones estructurales de hojas (batchUpdate)
    # ------------------------------------------------------------------
    def list_sheets(self, spreadsheet_id: str) -> list[tuple[int, str]] | None:
        """(sheetId, título) de todas las hojas del spreadsheet."""
        try:
            spreadsheet = execute(self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title))"
            ))
            return [
                (sheet["properties"]["sheetId"], sheet["properties"]["title"])
                for sheet in spreadsheet.get("sheets", [])
            ]
        except Exception as error:
            log_error("listando hojas del spreadsheet", error, f"spreadsheet_id={spreadsheet_id}")
            return None

    def _batch_update(self, spreadsheet_id: str, request: dict, context: str):
        try:
            return execute(self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [request]}
            ))
        except Exception as error:
            log_error(context, error, f"spreadsheet_id={spreadsheet_id} request={request}")
            return None

    def duplicate_sheet(self, spreadsheet_id: str, source_sheet_id: int, new_name: str) -> int | None:
        """Duplica una hoja dentro del mismo spreadsheet y la renombra.

        Devuelve el sheetId de la nueva hoja.
        """
        response = self._batch_update(
            spreadsheet_id,
            {"duplicateSheet": {"sourceSheetId": source_sheet_id, "newSheetName": new_name}},
            "duplicando hoja",
        )
        if response is None:
            return None
        return response["replies"][0]["duplicateSheet"]["properties"]["sheetId"]

    def delete_sheet(self, spreadsheet_id: str, sheet_id: int) -> bool:
        response = self._batch_update(
            spreadsheet_id, {"deleteSheet": {"sheetId": sheet_id}}, "eliminando hoja"
        )
        return response is not None

    def delete_rows(self, spreadsheet_id: str, sheet_id: int, first_row: int, last_row: int) -> bool:
        """Borra las filas [first_row, last_row] (1-indexed, inclusive) de una hoja."""
        response = self._batch_update(
            spreadsheet_id,
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": first_row - 1,
                        "endIndex": last_row,
                    }
                }
            },
            "borrando filas",
        )
        return response is not None
