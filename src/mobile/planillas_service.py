"""Planillas para la app: meses, planillas de un mes, la de hoy, resumen y crear/abrir.

Cuida la cuota de Google: los listados se cachean unos segundos y todo se lee
de forma perezosa (un mes solo se lista cuando la app lo abre).
"""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from accounting.accounting_service import AccountingService
from accounting.sheet_naming import MAX_DAILY_SHEETS, is_valid_date_name, sheet_name_for
from config.clock import DATE_FORMAT, today_str
from database.models import Business, BusinessContext
from drive.drive_client import DriveClient
from mobile.cache import TtlCache
from mobile.chat.chat_service import BotReply, to_replies
from mobile.chat.message_kinds import classify
from mobile.errors import BadGateway, Unprocessable
from mobile.google_gate import GoogleGate
from mobile.locks import KeyedLocks
from mobile.ownership import Ownership, PlanillaRef, planilla_ref
from mobile.values import int_or_none
from sheets.sheets_client import DailyTotals, SheetsClient

#: Atributo del layout -> (id para la app, nombre visible).
SECTION_NAMES = {
    "expense_region": ("compras", "Compras a proveedores"),
    "worker_loan_region": ("prestamos", "Préstamos a trabajadores"),
    "admin_region": ("administrador", "Vales del administrador"),
    "withdraw_region": ("retiros", "Retiros"),
    "investment_region": ("inversiones", "Inversiones"),
    "cleaning_region": ("aseo", "Aseo"),
    "feeding_region": ("alimentacion", "Alimentación"),
}

_DRIVE_ERROR = "No se pudieron leer las planillas en Google Drive. Intenta de nuevo."


@dataclass(frozen=True)
class MonthInfo:
    year: int
    month: int
    folder_name: str     # "noviembre-2026"

    @property
    def label(self) -> str:
        name, _, year = self.folder_name.partition("-")
        return f"{name.capitalize()} {year}"


@dataclass(frozen=True)
class TodayInfo:
    date: str
    planillas: list[PlanillaRef]       # por hoja (1, 2, 3…)
    totals: DailyTotals | None         # de la última hoja de hoy


@dataclass(frozen=True)
class SectionUsage:
    id: str
    label: str
    used: int | None
    capacity: int


@dataclass(frozen=True)
class Overview:
    planilla: PlanillaRef
    totals: DailyTotals
    sections: list[SectionUsage]


@dataclass(frozen=True)
class OpenResult:
    planilla: PlanillaRef
    created: bool
    replies: list[BotReply]


class PlanillasService:
    def __init__(
        self,
        accounting: AccountingService,
        drive: DriveClient,
        sheets: SheetsClient,
        ownership: Ownership,
        google: GoogleGate,
        locks: KeyedLocks,
        listings: TtlCache,
        today: Callable[[], str] = today_str,
    ):
        self._accounting = accounting
        self._drive = drive
        self._sheets = sheets
        self._ownership = ownership
        self._google = google
        self._locks = locks
        self._listings = listings
        self._today = today

    # ------------------------------------------------------------------
    # Lecturas (síncronas: los controladores las corren en un hilo)
    # ------------------------------------------------------------------
    def months(self, business: Business) -> list[MonthInfo]:
        """Carpetas de mes del negocio, de la más reciente a la más antigua."""
        self._google.ensure()

        def load():
            folders = self._drive.list_month_folders(business.sheets_folder_id)
            if folders is None:
                return None
            months = [MonthInfo(year, month, name) for _id, name, (year, month) in folders]
            return sorted(months, key=lambda m: (m.year, m.month), reverse=True)

        months = self._listings.get_or_load(("meses", business.id), load)
        if months is None:
            raise BadGateway(_DRIVE_ERROR, "DRIVE_NO_DISPONIBLE")
        return months

    def of_month(self, business: Business, year: int, month: int) -> list[PlanillaRef]:
        """Planillas de un mes: días de mayor a menor y, en un mismo día, hoja 1, 2, 3…"""
        self._google.ensure()
        if not 1 <= month <= 12 or not 2000 <= year <= 2100:
            raise Unprocessable("Mes o año inválido.", "MES_INVALIDO")

        def load():
            files = self._drive.list_planillas_of_month(business.sheets_folder_id, year, month)
            if files is None:
                return None
            refs = [ref for file_id, name in files if (ref := planilla_ref(file_id, name))]
            return sorted(refs, key=lambda r: (-_ordinal_day(r.date), r.ordinal))

        refs = self._listings.get_or_load(("mes", business.id, year, month), load)
        if refs is None:
            raise BadGateway(_DRIVE_ERROR, "DRIVE_NO_DISPONIBLE")
        return refs

    def today(self, business: Business) -> TodayInfo:
        """Planillas de hoy y los totales de la última (tarjeta de la pantalla Principal)."""
        date = self._today()
        day = datetime.strptime(date, DATE_FORMAT)
        planillas = sorted(
            (ref for ref in self.of_month(business, day.year, day.month) if ref.date == date),
            key=lambda r: r.ordinal,
        )
        totals = None
        if planillas:
            latest = planillas[-1]
            totals = self._listings.get_or_load(
                ("hoy", business.id, "totales", latest.id),
                lambda: self._sheets.get_daily_totals(latest.id),
            )
        return TodayInfo(date=date, planillas=planillas, totals=totals)

    def detail(self, business: Business, sheet_id: str) -> PlanillaRef:
        self._google.ensure()
        return self._ownership.planilla(business, sheet_id)

    def overview(self, business: Business, sheet_id: str) -> Overview:
        """Totales de la planilla y cuántas filas lleva cada sección (una sola lectura)."""
        ref = self.detail(business, sheet_id)
        overview = self._listings.get_or_load(
            ("totales", ref.id), lambda: self._sheets.get_planilla_overview(ref.id)
        )
        if overview is None:
            raise BadGateway("No se pudo leer la planilla en Google Sheets. Intenta de nuevo.",
                             "SHEETS_NO_DISPONIBLE")
        sections = []
        for attr, region in self._sheets.layout.daily_regions:
            section_id, label = SECTION_NAMES.get(attr, (attr, region.label))
            counter = int_or_none(overview.counters.get(attr))
            used = None if counter is None else max(0, min(region.capacity, counter - region.min_row))
            sections.append(SectionUsage(section_id, label, used, region.capacity))
        return Overview(planilla=ref, totals=overview.totals, sections=sections)

    # ------------------------------------------------------------------
    # Crear o abrir
    # ------------------------------------------------------------------
    async def open_or_create(self, ctx: BusinessContext, date: str, ordinal: int) -> OpenResult:
        """Abre la planilla de esa fecha y hoja, o la crea con los comandos del bot.

        Reutiliza `hoja <fecha>` / `<N> planilla <fecha>`: mismas reglas que por
        WhatsApp (orden de las hojas, saldo que pasa de la anterior, encabezado).
        Corre en una sesión temporal: no toca la conversación del chat.
        """
        self._google.ensure()
        date = (date or "").strip()
        if not is_valid_date_name(date):
            raise Unprocessable("La fecha debe tener el formato dd-mm-aaaa.", "FECHA_INVALIDA")
        if not 1 <= ordinal <= MAX_DAILY_SHEETS:
            raise Unprocessable(f"La hoja debe estar entre 1 y {MAX_DAILY_SHEETS}.", "HOJA_INVALIDA")

        business = ctx.business
        name = sheet_name_for(date, ordinal)
        command = f"hoja {date}" if ordinal == 1 else f"{ordinal} planilla {date}"
        phone = ctx.administrator.phone_number

        def run():
            existed = self._drive.find_sheet_by_name(business.sheets_folder_id, name) is not None
            responses, state = self._accounting.run_detached(phone, [command])
            return existed, responses, state

        # Dos toques seguidos en "Crear" no deben duplicar el archivo en Drive.
        async with self._locks.get(("crear-planilla", business.id, name)):
            existed, responses, state = await asyncio.to_thread(run)

        if state is None or state.active_sheet_id is None or state.active_sheet_name != name:
            reason = classify(responses[0])[1] if responses else "No se pudo abrir la planilla."
            raise Unprocessable(reason, "NO_SE_PUDO_ABRIR")

        if not existed:
            self._listings.invalidate(lambda k: len(k) > 1 and k[0] in ("meses", "mes", "hoy") and k[1] == business.id)
        return OpenResult(
            planilla=PlanillaRef(id=state.active_sheet_id, name=name, date=date, ordinal=ordinal),
            created=not existed,
            replies=to_replies(responses, None),
        )


def _ordinal_day(date: str) -> int:
    return datetime.strptime(date, DATE_FORMAT).toordinal()
