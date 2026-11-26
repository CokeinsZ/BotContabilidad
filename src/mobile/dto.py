"""Contrato JSON de la API de la app (`/app`).

Claves en español y snake_case: son las palabras del negocio y de los
comandos. Este es el ÚNICO lugar que conoce la forma del JSON; los servicios
devuelven dataclasses y aquí se convierten.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from accounting.session_manager import SessionState
from mobile.auth import IssuedSession, PairingPoll, PairingStart
from mobile.catalog import CatalogEntry
from mobile.chat import BotReply, ChatResult
from mobile.ownership import PlanillaRef, WorkerRef
from mobile.planillas_service import MonthInfo, OpenResult, Overview, TodayInfo
from mobile.profile_service import Profile
from mobile.values import folder_url, number_or_none
from mobile.workers_service import ArchivedDetail, ArchivedRef, Vale, WorkerDetail, WorkersList
from sheets.sheets_client import DailyTotals

_CREATE_OPTION_PREFIX = "Crear nuevo trabajador"


# ----------------------------------------------------------------------
# Peticiones
# ----------------------------------------------------------------------
class VinculacionRequest(BaseModel):
    dispositivo: str | None = Field(default=None, max_length=80)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class NombreRequest(BaseModel):
    nombre: str = Field(max_length=200)


class CrearPlanillaRequest(BaseModel):
    fecha: str = Field(max_length=10, description="dd-mm-aaaa")
    hoja: int = Field(default=1, ge=1, le=31)


class MensajeRequest(BaseModel):
    client_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    comando: str | None = Field(default=None, max_length=40)
    texto: str = Field(default="", max_length=500)


class SeleccionRequest(BaseModel):
    opcion: int = Field(ge=1, le=100)


# ----------------------------------------------------------------------
# Respuestas
# ----------------------------------------------------------------------
class ErrorOut(BaseModel):
    detail: str
    codigo: str


class AdministradorOut(BaseModel):
    id: int
    nombre: str
    identificador: str


class CompaneroOut(BaseModel):
    id: int
    nombre: str
    es_usted: bool


class NegocioOut(BaseModel):
    id: int
    nombre: str
    carpeta_planillas_url: str
    carpeta_trabajadores_url: str | None


class PerfilOut(BaseModel):
    administrador: AdministradorOut
    negocio: NegocioOut
    administradores: list[CompaneroOut]
    hoy: str
    google_conectado: bool
    whatsapp_bot: str | None


class SesionOut(BaseModel):
    access_token: str
    expira_en: int = Field(description="segundos de vida del access_token")
    refresh_token: str
    perfil: PerfilOut


class VinculacionOut(BaseModel):
    vinculacion_id: str
    codigo: str
    mensaje: str
    whatsapp_url: str | None
    expira_en: int = Field(description="segundos que le quedan al código")


class EstadoVinculacionOut(BaseModel):
    estado: str = Field(description="pendiente | confirmada | consumida | expirada")
    sesion: SesionOut | None = None


class ComandoOut(BaseModel):
    id: str
    etiqueta: str
    icono: str
    argumentos: str = Field(description="ninguno | monto | monto_texto | monto_trabajador")
    ejemplo: str
    ayuda: str
    confirmar: bool
    sugiere_trabajador: bool
    alias: list[str]


class MesOut(BaseModel):
    anio: int
    mes: int
    carpeta: str
    etiqueta: str


class PlanillaOut(BaseModel):
    id: str
    nombre: str
    fecha: str
    hoja: int
    url: str


#: Montos: enteros cuando lo son (5000, no 5000.0).
Monto = int | float | None


class TotalesOut(BaseModel):
    gastos: Monto
    efectivo: Monto
    venta_total: Monto
    saldo_previo: Monto
    saldo_total: Monto


class HoyOut(BaseModel):
    fecha: str
    planillas: list[PlanillaOut]
    ultima: PlanillaOut | None
    totales: TotalesOut | None


class SeccionOut(BaseModel):
    id: str
    etiqueta: str
    usadas: int | None
    capacidad: int


class ResumenOut(BaseModel):
    planilla: PlanillaOut
    totales: TotalesOut
    secciones: list[SeccionOut]


class RespuestaOut(BaseModel):
    tipo: str = Field(description="exito | aviso | error | info | seleccion")
    texto: str


class AbrirPlanillaOut(BaseModel):
    planilla: PlanillaOut
    creada: bool
    mensajes: list[RespuestaOut]


class OpcionOut(BaseModel):
    valor: int
    etiqueta: str
    crea: bool


class SeleccionOut(BaseModel):
    pregunta: str
    opciones: list[OpcionOut]
    comando: str = Field(description="lo que se cancela si no se responde")
    planilla_id: str | None
    planilla_nombre: str | None


class EstadoChatOut(BaseModel):
    seleccion: SeleccionOut | None
    deshacer: str | None


class ResultadoChatOut(BaseModel):
    client_id: str | None
    comandos: list[str]
    interpretado_por_ia: bool
    respuestas: list[RespuestaOut]
    estado: EstadoChatOut
    procesado_en: datetime


class TrabajadorOut(BaseModel):
    id: str
    nombre: str


class TrabajadoresOut(BaseModel):
    carpeta_configurada: bool
    trabajadores: list[TrabajadorOut]


class ValeOut(BaseModel):
    fila: int
    fecha: str | None
    monto: Monto
    nota: str | None


class NominaRefOut(BaseModel):
    hoja_id: int
    titulo: str
    fecha: str | None


class TrabajadorDetalleOut(BaseModel):
    id: str
    nombre: str
    url: str
    total_prestamos: Monto
    vales: list[ValeOut]
    usados: int
    capacidad: int
    nominas: list[NominaRefOut]


class NominaDetalleOut(BaseModel):
    trabajador: TrabajadorOut
    nomina: NominaRefOut
    url: str
    total_prestamos: Monto
    vales: list[ValeOut]


# ----------------------------------------------------------------------
# Conversores
# ----------------------------------------------------------------------
def perfil_out(profile: Profile) -> PerfilOut:
    admin, business = profile.context.administrator, profile.context.business
    return PerfilOut(
        administrador=AdministradorOut(id=admin.id, nombre=admin.name, identificador=admin.phone_number),
        negocio=NegocioOut(
            id=business.id,
            nombre=business.name,
            carpeta_planillas_url=folder_url(business.sheets_folder_id),
            carpeta_trabajadores_url=folder_url(business.workers_folder_id) if business.workers_folder_id else None,
        ),
        administradores=[
            CompaneroOut(id=a.id, nombre=a.name, es_usted=a.id == admin.id) for a in profile.administrators
        ],
        hoy=profile.today,
        google_conectado=profile.google_connected,
        whatsapp_bot=profile.bot_whatsapp_number or None,
    )


def sesion_out(issued: IssuedSession, profile: Profile) -> SesionOut:
    return SesionOut(
        access_token=issued.access_token,
        expira_en=issued.access_expires_in,
        refresh_token=issued.refresh_token,
        perfil=perfil_out(profile),
    )


def vinculacion_out(start: PairingStart) -> VinculacionOut:
    return VinculacionOut(
        vinculacion_id=start.id,
        codigo=start.code,
        mensaje=start.message,
        whatsapp_url=start.whatsapp_url,
        expira_en=start.expires_in,
    )


def estado_vinculacion_out(poll: PairingPoll, profile: Profile | None) -> EstadoVinculacionOut:
    sesion = sesion_out(poll.session, profile) if poll.session and profile else None
    return EstadoVinculacionOut(estado=poll.state, sesion=sesion)


def comando_out(entry: CatalogEntry, aliases: list[str]) -> ComandoOut:
    return ComandoOut(
        id=entry.id, etiqueta=entry.label, icono=entry.icon, argumentos=entry.args,
        ejemplo=entry.example, ayuda=entry.help, confirmar=entry.confirm,
        sugiere_trabajador=entry.suggests_worker, alias=aliases,
    )


def mes_out(month: MonthInfo) -> MesOut:
    return MesOut(anio=month.year, mes=month.month, carpeta=month.folder_name, etiqueta=month.label)


def planilla_out(ref: PlanillaRef) -> PlanillaOut:
    return PlanillaOut(id=ref.id, nombre=ref.name, fecha=ref.date, hoja=ref.ordinal, url=ref.url)


def totales_out(totals: DailyTotals) -> TotalesOut:
    return TotalesOut(
        gastos=number_or_none(totals.total_expenses),
        efectivo=number_or_none(totals.day_cash),
        venta_total=number_or_none(totals.total_sales),
        saldo_previo=number_or_none(totals.previous_balance),
        saldo_total=number_or_none(totals.total_balance),
    )


def hoy_out(today: TodayInfo) -> HoyOut:
    planillas = [planilla_out(ref) for ref in today.planillas]
    return HoyOut(
        fecha=today.date,
        planillas=planillas,
        ultima=planillas[-1] if planillas else None,
        totales=totales_out(today.totals) if today.totals else None,
    )


def resumen_out(overview: Overview) -> ResumenOut:
    return ResumenOut(
        planilla=planilla_out(overview.planilla),
        totales=totales_out(overview.totals),
        secciones=[
            SeccionOut(id=s.id, etiqueta=s.label, usadas=s.used, capacidad=s.capacity)
            for s in overview.sections
        ],
    )


def respuesta_out(reply: BotReply) -> RespuestaOut:
    return RespuestaOut(tipo=reply.kind, texto=reply.text)


def abrir_planilla_out(result: OpenResult) -> AbrirPlanillaOut:
    return AbrirPlanillaOut(
        planilla=planilla_out(result.planilla),
        creada=result.created,
        mensajes=[respuesta_out(r) for r in result.replies],
    )


def estado_chat_out(state: SessionState | None) -> EstadoChatOut:
    if state is None:
        return EstadoChatOut(seleccion=None, deshacer=None)
    selection = state.selection
    seleccion = None
    if selection is not None:
        labels = list(selection.option_labels)
        labels += [f"Opción {n}" for n in range(len(labels) + 1, selection.options + 1)]
        seleccion = SeleccionOut(
            pregunta=selection.prompt or selection.menu,
            opciones=[
                OpcionOut(valor=n, etiqueta=label, crea=label.startswith(_CREATE_OPTION_PREFIX))
                for n, label in enumerate(labels[: selection.options], start=1)
            ],
            comando=selection.description,
            planilla_id=selection.sheet_id,
            planilla_nombre=selection.sheet_name,
        )
    return EstadoChatOut(seleccion=seleccion, deshacer=state.undo_description)


def resultado_chat_out(result: ChatResult) -> ResultadoChatOut:
    return ResultadoChatOut(
        client_id=result.client_id,
        comandos=result.commands,
        interpretado_por_ia=result.used_ai,
        respuestas=[respuesta_out(r) for r in result.replies],
        estado=estado_chat_out(result.state),
        procesado_en=result.processed_at,
    )


def trabajador_out(worker: WorkerRef) -> TrabajadorOut:
    return TrabajadorOut(id=worker.id, nombre=worker.name)


def trabajadores_out(workers: WorkersList) -> TrabajadoresOut:
    return TrabajadoresOut(
        carpeta_configurada=workers.folder_configured,
        trabajadores=[trabajador_out(w) for w in workers.workers],
    )


def vale_out(vale: Vale) -> ValeOut:
    return ValeOut(fila=vale.row, fecha=vale.date, monto=vale.amount, nota=vale.note)


def nomina_ref_out(ref: ArchivedRef) -> NominaRefOut:
    return NominaRefOut(hoja_id=ref.sheet_gid, titulo=ref.title, fecha=ref.date)


def trabajador_detalle_out(detail: WorkerDetail) -> TrabajadorDetalleOut:
    return TrabajadorDetalleOut(
        id=detail.worker.id,
        nombre=detail.worker.name,
        url=detail.worker.url,
        total_prestamos=detail.total,
        vales=[vale_out(v) for v in detail.vales],
        usados=detail.used,
        capacidad=detail.capacity,
        nominas=[nomina_ref_out(r) for r in detail.archived],
    )


def nomina_detalle_out(detail: ArchivedDetail) -> NominaDetalleOut:
    return NominaDetalleOut(
        trabajador=trabajador_out(detail.worker),
        nomina=nomina_ref_out(detail.archive),
        url=f"{detail.worker.url}#gid={detail.archive.sheet_gid}",
        total_prestamos=detail.total,
        vales=[vale_out(v) for v in detail.vales],
    )
