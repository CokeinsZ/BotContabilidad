"""Trabajadores para la app: lista, período actual (vales) y nóminas archivadas.

La lista solo trae nombres: leer el total de cada trabajador costaría una
lectura de Google por archivo. El detalle lee todo de un archivo en dos
llamadas (valores + lista de hojas).
"""
from dataclasses import dataclass
from datetime import datetime

from accounting.names import name_key
from accounting.sheet_naming import is_valid_date_name
from config.clock import DATE_FORMAT
from database.models import Business
from drive.drive_client import DriveClient
from mobile.cache import TtlCache
from mobile.errors import BadGateway, NotFound
from mobile.google_gate import GoogleGate
from mobile.ownership import Ownership, WorkerRef
from mobile.values import int_or_none, number_or_none
from sheets.a1 import cell_at, parse_cell, split_sheet
from sheets.layout import SheetRegion, sheet_prefix
from sheets.sheets_client import SheetsClient

_SHEETS_ERROR = "No se pudo leer el archivo del trabajador en Google Sheets. Intenta de nuevo."


@dataclass(frozen=True)
class WorkersList:
    folder_configured: bool
    workers: list[WorkerRef]


@dataclass(frozen=True)
class Vale:
    row: int
    date: str | None
    amount: int | float | None
    note: str | None


@dataclass(frozen=True)
class ArchivedRef:
    sheet_gid: int
    title: str           # "24-11-2026" o "24-11-2026 (2)"
    date: str | None     # "24-11-2026" (None si el título no es una fecha)


@dataclass(frozen=True)
class WorkerDetail:
    worker: WorkerRef
    total: int | float | None   # suma de préstamos del período (B30)
    vales: list[Vale]
    used: int
    capacity: int
    archived: list[ArchivedRef]


@dataclass(frozen=True)
class ArchivedDetail:
    worker: WorkerRef
    archive: ArchivedRef
    total: int | float | None
    vales: list[Vale]


class WorkersService:
    def __init__(
        self,
        drive: DriveClient,
        sheets: SheetsClient,
        ownership: Ownership,
        google: GoogleGate,
        listings: TtlCache,
    ):
        self._drive = drive
        self._sheets = sheets
        self._ownership = ownership
        self._google = google
        self._listings = listings

    def list(self, business: Business) -> WorkersList:
        if not business.workers_folder_id:
            return WorkersList(folder_configured=False, workers=[])
        self._google.ensure()

        def load():
            files = self._drive.try_list_files_in_folder(business.workers_folder_id)
            if files is None:
                return None
            workers = [WorkerRef(id=file_id, name=name) for file_id, name in files]
            return sorted(workers, key=lambda w: name_key(w.name))

        workers = self._listings.get_or_load(("trabajadores", business.id), load)
        if workers is None:
            raise BadGateway("No se pudieron leer los trabajadores en Google Drive. Intenta de nuevo.",
                             "DRIVE_NO_DISPONIBLE")
        return WorkersList(folder_configured=True, workers=workers)

    def detail(self, business: Business, file_id: str) -> WorkerDetail:
        self._google.ensure()
        worker = self._ownership.worker(business, file_id)
        layout = self._sheets.layout
        region = layout.worker_file_region
        block = region.block_range(region.min_row, region.max_row)
        ranges = [block, layout.worker_loan_sum_cell, region.counter_cell]

        values = self._sheets.get_values(worker.id, ranges)
        sheets_list = self._sheets.list_sheets(worker.id)
        if values is None or sheets_list is None:
            raise BadGateway(_SHEETS_ERROR, "SHEETS_NO_DISPONIBLE")

        vales = _parse_vales(values.get(block, []), region)
        counter = int_or_none(_first(values, region.counter_cell))
        used = max(0, min(region.capacity, counter - region.min_row)) if counter is not None else len(vales)
        archived = [
            _archived_ref(gid, title)
            for gid, title in sheets_list
            if title.strip().lower() != layout.worker_main_sheet
        ]
        archived.sort(key=_archive_sort_key, reverse=True)
        return WorkerDetail(
            worker=worker,
            total=number_or_none(_first(values, layout.worker_loan_sum_cell)),
            vales=vales,
            used=used,
            capacity=region.capacity,
            archived=archived,
        )

    def archived(self, business: Business, file_id: str, sheet_gid: int) -> ArchivedDetail:
        """Vales y total de una nómina archivada (copia de "principal" sin las filas 1–9)."""
        self._google.ensure()
        worker = self._ownership.worker(business, file_id)
        layout = self._sheets.layout
        sheets_list = self._sheets.list_sheets(worker.id)
        if sheets_list is None:
            raise BadGateway(_SHEETS_ERROR, "SHEETS_NO_DISPONIBLE")
        title = next((t for gid, t in sheets_list if gid == sheet_gid), None)
        if title is None or title.strip().lower() == layout.worker_main_sheet:
            raise NotFound("Esa nómina no existe en el archivo del trabajador.", "NOMINA_NO_EXISTE")

        offset = layout.worker_archive_offset
        prefix = sheet_prefix(title)
        region = layout.worker_file_region.moved(prefix, offset)
        _, sum_cell = split_sheet(layout.worker_loan_sum_cell)
        column, row = parse_cell(sum_cell)
        total_cell = cell_at(prefix, column, row - offset)
        block = region.block_range(region.min_row, region.max_row)

        values = self._sheets.get_values(worker.id, [block, total_cell])
        if values is None:
            raise BadGateway(_SHEETS_ERROR, "SHEETS_NO_DISPONIBLE")
        return ArchivedDetail(
            worker=worker,
            archive=_archived_ref(sheet_gid, title),
            total=number_or_none(_first(values, total_cell)),
            vales=_parse_vales(values.get(block, []), region),
        )


def _first(values: dict, cell: str):
    rows = values.get(cell, [])
    return rows[0][0] if rows and rows[0] else None


def _parse_vales(rows: list[list], region: SheetRegion) -> list[Vale]:
    """Filas con vale: fecha escrita o monto distinto de 0 (la plantilla trae 0)."""
    vales = []
    for index, row in enumerate(rows):
        cells = list(row) + [""] * (region.width - len(row))
        date, amount = cells[0], cells[1] if region.width > 1 else None
        note = cells[2] if region.width > 2 else None
        amount_number = number_or_none(amount)
        if date in ("", None) and not amount_number:
            continue
        vales.append(Vale(
            row=region.min_row + index,
            date=str(date) if date not in ("", None) else None,
            amount=amount_number,
            note=str(note) if note not in ("", None) else None,
        ))
    return vales


def _archived_ref(gid: int, title: str) -> ArchivedRef:
    base = title.strip()[:10]
    return ArchivedRef(sheet_gid=gid, title=title, date=base if is_valid_date_name(base) else None)


def _archive_sort_key(ref: ArchivedRef) -> tuple:
    """Más reciente primero; "24-11-2026 (2)" va antes que "24-11-2026"."""
    day = datetime.strptime(ref.date, DATE_FORMAT).toordinal() if ref.date else 0
    suffix = ref.title.strip()[10:].strip(" ()")
    return day, int(suffix) if suffix.isdigit() else 1, ref.title
