"""Verifica que una planilla o un archivo de trabajador sea del negocio.

La app manda ids de archivos de Drive. Sin esta verificación, un
administrador podría leer o escribir la planilla de OTRO negocio con solo
conocer su id. Los resultados positivos se cachean (los archivos no cambian
de carpeta).
"""
import re
from dataclasses import dataclass

from accounting.sheet_naming import parse_sheet_name
from database.models import Business
from drive.drive_client import DriveClient
from mobile.cache import TtlCache
from mobile.errors import NotFound
from mobile.values import sheet_url

SHEET_MIME = "application/vnd.google-apps.spreadsheet"
_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,200}$")


@dataclass(frozen=True)
class PlanillaRef:
    id: str
    name: str         # "24-11-2026-2"
    date: str         # "24-11-2026"
    ordinal: int      # 2

    @property
    def url(self) -> str:
        return sheet_url(self.id)


@dataclass(frozen=True)
class WorkerRef:
    id: str
    name: str

    @property
    def url(self) -> str:
        return sheet_url(self.id)


def planilla_ref(file_id: str, name: str) -> PlanillaRef | None:
    """PlanillaRef si el nombre es de una planilla diaria (dd-mm-aaaa[-N])."""
    parsed = parse_sheet_name(name)
    if parsed is None:
        return None
    day, ordinal = parsed
    return PlanillaRef(id=file_id, name=name, date=day.strftime("%d-%m-%Y"), ordinal=ordinal)


class Ownership:
    def __init__(self, drive: DriveClient, cache: TtlCache | None = None):
        self._drive = drive
        self._cache = cache or TtlCache(ttl_seconds=24 * 3600, max_items=5000)

    def planilla(self, business: Business, sheet_id: str) -> PlanillaRef:
        """La planilla si está en una carpeta de mes del negocio; si no, 404."""
        key = ("planilla", business.id, sheet_id)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        not_found = NotFound("La planilla no existe o no es de este negocio.", "PLANILLA_NO_EXISTE")
        meta = self._sheet_meta(sheet_id)
        ref = planilla_ref(sheet_id, meta["name"]) if meta else None
        if ref is None:
            raise not_found
        in_business = any(
            business.sheets_folder_id in ((self._drive.get_file(parent) or {}).get("parents") or [])
            for parent in meta.get("parents") or []
        )
        if not in_business:
            raise not_found
        self._cache.set(key, ref)
        return ref

    def worker(self, business: Business, file_id: str) -> WorkerRef:
        """El archivo del trabajador si está en la carpeta de trabajadores del negocio."""
        key = ("trabajador", business.id, file_id)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        meta = self._sheet_meta(file_id)
        folder = business.workers_folder_id
        if meta is None or not folder or folder not in (meta.get("parents") or []):
            raise NotFound("El trabajador no existe o no es de este negocio.", "TRABAJADOR_NO_EXISTE")
        ref = WorkerRef(id=file_id, name=meta["name"])
        self._cache.set(key, ref)
        return ref

    def _sheet_meta(self, file_id: str) -> dict | None:
        if not _FILE_ID_RE.match(file_id or ""):
            return None
        meta = self._drive.get_file(file_id)
        if not meta or meta.get("trashed") or meta.get("mimeType") != SHEET_MIME:
            return None
        return meta
