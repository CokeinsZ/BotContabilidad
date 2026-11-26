"""Fakes en memoria de las APIs de Google Sheets / Drive.

Imitan el comportamiento relevante de la API real:
- render UNFORMATTED_VALUE / FORMULA,
- valueInputOption RAW (texto tal cual) / USER_ENTERED (fórmulas),
- filas y columnas vacías al final se recortan en las respuestas,
- fórmulas simples `=SUM(B13:B29)` y `=B39+B42-E60` se evalúan.
"""
import copy
import re
import threading
import time

from sheets.a1 import cell_at, column_number, parse_cell, split_sheet
from sheets.sheets_client import SheetsClient

_REF = re.compile(r"([A-Z]+\d+)(?::([A-Z]+\d+))?")


class _Exec:
    def __init__(self, fn):
        self._fn = fn

    def execute(self):
        return self._fn()


class FakeSpreadsheet:
    def __init__(self, sheets: dict[str, dict] | None = None):
        # título -> {"id": int, "cells": {(col, row): valor}}
        self.sheets: dict[str, dict] = {}
        self._next_id = 0
        for title, cells in (sheets or {"Hoja 1": {}}).items():
            self.add_sheet(title, cells)

    def add_sheet(self, title: str, cells: dict | None = None) -> int:
        sheet_id = self._next_id
        self._next_id += 1
        self.sheets[title] = {"id": sheet_id, "cells": dict(cells or {})}
        return sheet_id

    def first_title(self) -> str:
        return next(iter(self.sheets))

    def by_id(self, sheet_id: int) -> str:
        return next(t for t, s in self.sheets.items() if s["id"] == sheet_id)

    # --- acceso por A1 ---------------------------------------------------
    def _resolve(self, range_a1: str):
        prefix, cells = split_sheet(range_a1)
        title = prefix[:-1].strip("'") if prefix else self.first_title()
        first, _, last = cells.partition(":")
        c1, r1 = parse_cell(first)
        c2, r2 = parse_cell(last or first)
        return self.sheets[title]["cells"], c1, r1, c2, r2

    def raw(self, range_a1: str):
        cells, c, r, *_ = self._resolve(range_a1)
        return cells.get((c, r), "")

    def evaluate(self, cells: dict, value):
        if not (isinstance(value, str) and value.startswith("=")):
            return value
        expr = value[1:]

        def ref_value(match):
            first, last = match.group(1), match.group(2)
            c1, r1 = parse_cell(first)
            c2, r2 = parse_cell(last or first)
            total = 0
            for row in range(r1, r2 + 1):
                for col in range(c1, c2 + 1):
                    v = self.evaluate(cells, cells.get((col, row), ""))
                    total += v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0
            return str(total)

        expr = expr.replace("SUM", "")
        expr = _REF.sub(ref_value, expr)
        return eval(expr, {"__builtins__": {}})  # noqa: S307 (solo tests)

    def read(self, range_a1: str, render: str) -> list[list]:
        cells, c1, r1, c2, r2 = self._resolve(range_a1)
        rows = []
        for row in range(r1, r2 + 1):
            values = []
            for col in range(c1, c2 + 1):
                value = cells.get((col, row), "")
                if render != "FORMULA":
                    value = self.evaluate(cells, value)
                values.append(value)
            while values and values[-1] == "":
                values.pop()
            rows.append(values)
        while rows and not rows[-1]:
            rows.pop()
        return rows

    def write(self, range_a1: str, values: list[list], option: str) -> int:
        cells, c1, r1, *_ = self._resolve(range_a1)
        count = 0
        for i, row in enumerate(values):
            for j, value in enumerate(row):
                key = (c1 + j, r1 + i)
                if option == "USER_ENTERED" and isinstance(value, str) and not value.startswith("="):
                    try:
                        value = float(value) if "." in value else int(value)
                    except ValueError:
                        pass
                if value == "" or value is None:
                    cells.pop(key, None)
                elif option == "RAW" and isinstance(value, str) and value.startswith("="):
                    cells[key] = "'" + value  # RAW guarda la fórmula como texto
                else:
                    cells[key] = value
                count += 1
        return count


class FakeSheetsClient(SheetsClient):
    """SheetsClient real sobre el servicio falso."""

    def __init__(self, service):
        super().__init__(auth_manager=None)
        self._fake_service = service

    @property
    def service(self):
        return self._fake_service


class FakeSheetsService:
    """Imita `build("sheets", "v4")` lo suficiente para SheetsClient."""

    def __init__(self, read_delay: float = 0.0):
        self.files: dict[str, FakeSpreadsheet] = {}
        self.read_delay = read_delay
        self.calls: list[str] = []
        self._guard = threading.Lock()

    # encadenamiento estilo googleapiclient
    def spreadsheets(self):
        return self

    def values(self):
        return _Values(self)

    def get(self, spreadsheetId, fields=None, **_):
        def run():
            book = self.files[spreadsheetId]
            return {"sheets": [{"properties": {"sheetId": s["id"], "title": t}} for t, s in book.sheets.items()]}
        return _Exec(run)

    def batchUpdate(self, spreadsheetId, body):
        def run():
            book = self.files[spreadsheetId]
            replies = []
            for request in body["requests"]:
                if "duplicateSheet" in request:
                    req = request["duplicateSheet"]
                    if req["newSheetName"] in book.sheets:
                        raise RuntimeError("A sheet with that name already exists")
                    source = book.sheets[book.by_id(req["sourceSheetId"])]
                    new_id = book.add_sheet(req["newSheetName"], copy.deepcopy(source["cells"]))
                    replies.append({"duplicateSheet": {"properties": {"sheetId": new_id}}})
                elif "deleteSheet" in request:
                    del book.sheets[book.by_id(request["deleteSheet"]["sheetId"])]
                    replies.append({})
                elif "deleteDimension" in request:
                    rng = request["deleteDimension"]["range"]
                    sheet = book.sheets[book.by_id(rng["sheetId"])]
                    start, end = rng["startIndex"] + 1, rng["endIndex"]  # filas 1-indexed incl.
                    removed = end - start + 1
                    sheet["cells"] = {
                        (c, r if r < start else r - removed): v
                        for (c, r), v in sheet["cells"].items()
                        if not (start <= r <= end)
                    }
                    replies.append({})
            return {"replies": replies}
        return _Exec(run)


class _Values:
    def __init__(self, service: FakeSheetsService):
        self._s = service

    def batchGet(self, spreadsheetId, ranges, valueRenderOption="FORMATTED_VALUE"):
        def run():
            if self._s.read_delay:
                time.sleep(self._s.read_delay)
            book = self._s.files[spreadsheetId]
            self._s.calls.append("batchGet")
            return {"valueRanges": [{"range": r, "values": book.read(r, valueRenderOption)} for r in ranges]}
        return _Exec(run)

    def batchUpdate(self, spreadsheetId, body):
        def run():
            book = self._s.files[spreadsheetId]
            self._s.calls.append("batchUpdate")
            total = sum(book.write(d["range"], d["values"], body["valueInputOption"]) for d in body["data"])
            return {"totalUpdatedCells": total}
        return _Exec(run)


# ----------------------------------------------------------------------
# Plantillas reales (resumidas) tomadas de Formato_Planilla / Formato_Trabajadores
# ----------------------------------------------------------------------
def planilla_template() -> dict:
    cells = {
        (2, 38): "=B35+D27+D35+E35+SUM(E10:E18)+SUM(E20:E24)",
        (2, 35): "=SUM(B11:B34)", (4, 27): "=SUM(D11:D26)", (4, 35): "=SUM(D29:D34)",
        (5, 35): "=SUM(E26:E34)", (5, 60): "=SUM(E39:E59)",
        (2, 39): 0, (2, 40): "=B38+B39", (2, 42): 0, (2, 58): "=B39+B42-E60",
    }
    for row, counter in [(135, 11), (136, 11), (137, 26), (138, 39), (139, 29), (140, 11), (141, 20)]:
        cells[(3, row)] = counter
    return {"Hoja 1": cells}


def workers_template() -> dict:
    cells = {(2, row): 0 for row in range(13, 29)}
    cells[(2, 30)] = "=SUM(B13:B29)"
    cells[(3, 123)] = 13
    return {"principal": cells}


SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
MONTH_NAMES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def month_folder_of(sheet_name: str) -> str:
    """'24-11-2026-2' -> 'noviembre-2026'."""
    day, month, year = sheet_name[:10].split("-")
    return f"{MONTH_NAMES[int(month) - 1]}-{year}"


class FakeDrive:
    """Imita DriveClient sobre FakeSheetsService.

    Las planillas viven en carpetas de mes "month:<mes-aaaa>" dentro de
    `sheets_folder_id`; los trabajadores, en `workers_folder_id`.
    `foreign` guarda archivos de OTROS negocios (para probar pertenencia).
    """

    service = object()

    def __init__(self, sheets_service: FakeSheetsService,
                 sheets_folder_id: str = "folder-planillas",
                 workers_folder_id: str = "folder-trabajadores"):
        self._sheets = sheets_service
        self.sheets_folder_id = sheets_folder_id
        self.workers_folder_id = workers_folder_id
        self.planillas: dict[str, str] = {}          # nombre -> id
        self.workers: list[tuple[str, str]] = []     # (id, nombre)
        self.foreign: dict[str, dict] = {}           # id -> metadatos de otro negocio
        self._counter = 0

    def _new_file(self, template: dict) -> str:
        self._counter += 1
        file_id = f"file-{self._counter}"
        self._sheets.files[file_id] = FakeSpreadsheet(copy.deepcopy(template))
        return file_id

    def find_sheet_by_name(self, folder_id, name):
        return self.planillas.get(name)

    def duplicate_template(self, folder_id, name):
        file_id = self._new_file(planilla_template())
        self.planillas[name] = file_id
        return file_id, name

    def find_daily_sheets(self, folder_id, date_str):
        def ordinal(name):
            return 1 if name == date_str else int(name.rsplit("-", 1)[1])
        found = [(i, n) for n, i in self.planillas.items() if n[:10] == date_str]
        return sorted(found, key=lambda item: ordinal(item[1]))

    def list_files_in_folder(self, folder_id):
        return list(self.workers)

    def list_planillas_from(self, folder_id, from_date):
        return [(file_id, name) for name, file_id in self.planillas.items()]

    def add_worker(self, name: str) -> str:
        file_id = self._new_file(workers_template())
        self.workers.append((file_id, name))
        return file_id

    def duplicate_workers_template(self, folder_id, name):
        return self.add_worker(name), name

    # --- lo que usa la API de la app ----------------------------------
    def try_list_files_in_folder(self, folder_id):
        return list(self.workers)

    def list_month_folders(self, folder_id):
        months = {month_folder_of(name) for name in self.planillas}
        result = []
        for month in months:
            name, _, year = month.partition("-")
            result.append((f"month:{month}", month, (int(year), MONTH_NAMES.index(name) + 1)))
        return result

    def list_planillas_of_month(self, folder_id, year, month):
        wanted = f"{MONTH_NAMES[month - 1]}-{year}"
        return [(file_id, name) for name, file_id in self.planillas.items()
                if month_folder_of(name) == wanted]

    def get_file(self, file_id):
        if file_id in self.foreign:
            return self.foreign[file_id]
        for name, planilla_id in self.planillas.items():
            if planilla_id == file_id:
                return {"id": file_id, "name": name, "mimeType": SHEET_MIME, "trashed": False,
                        "parents": [f"month:{month_folder_of(name)}"]}
        if file_id.startswith("month:"):
            return {"id": file_id, "name": file_id[6:], "mimeType": FOLDER_MIME, "trashed": False,
                    "parents": [self.sheets_folder_id]}
        for worker_id, name in self.workers:
            if worker_id == file_id:
                return {"id": file_id, "name": name, "mimeType": SHEET_MIME, "trashed": False,
                        "parents": [self.workers_folder_id]}
        return None


def cell_value(service: FakeSheetsService, file_id: str, a1: str):
    return service.files[file_id].raw(a1)


def col_values(service: FakeSheetsService, file_id: str, a1_range: str, render="UNFORMATTED_VALUE"):
    return service.files[file_id].read(a1_range, render)


__all__ = [
    "FOLDER_MIME",
    "SHEET_MIME",
    "month_folder_of",
    "FakeDrive",
    "FakeSheetsClient", "FakeSheetsService", "FakeSpreadsheet", "cell_at", "cell_value",
    "col_values", "column_number", "planilla_template", "workers_template",
]
