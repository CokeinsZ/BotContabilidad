"""Planillas: meses, planillas de un mes, la de hoy, crear/abrir, detalle y resumen."""
import asyncio

from fastapi import APIRouter, Depends, Query

from database.models import BusinessContext
from mobile.dto import (
    AbrirPlanillaOut,
    CrearPlanillaRequest,
    HoyOut,
    MesOut,
    PlanillaOut,
    ResumenOut,
    abrir_planilla_out,
    hoy_out,
    mes_out,
    planilla_out,
    resumen_out,
)
from mobile.planillas_service import PlanillasService
from mobile.security.dependencies import CurrentContext


def create_planillas_router(planillas: PlanillasService, current: CurrentContext) -> APIRouter:
    router = APIRouter(prefix="/planillas", tags=["App · Planillas"])

    # Las rutas fijas van antes que /{planilla_id}.
    @router.get("/meses", response_model=list[MesOut])
    async def months(ctx: BusinessContext = Depends(current)):
        """Carpetas mes-aaaa del negocio, de la más reciente a la más antigua."""
        return [mes_out(m) for m in await asyncio.to_thread(planillas.months, ctx.business)]

    @router.get("/hoy", response_model=HoyOut)
    async def today(ctx: BusinessContext = Depends(current)):
        """Planillas de hoy y los totales de la última hoja."""
        return hoy_out(await asyncio.to_thread(planillas.today, ctx.business))

    @router.get("", response_model=list[PlanillaOut])
    async def of_month(
        anio: int = Query(ge=2000, le=2100),
        mes: int = Query(ge=1, le=12),
        ctx: BusinessContext = Depends(current),
    ):
        """Planillas de un mes ([] si la carpeta del mes no existe)."""
        refs = await asyncio.to_thread(planillas.of_month, ctx.business, anio, mes)
        return [planilla_out(ref) for ref in refs]

    @router.post("", response_model=AbrirPlanillaOut)
    async def open_or_create(body: CrearPlanillaRequest, ctx: BusinessContext = Depends(current)):
        """Abre la planilla de esa fecha y hoja, o la crea con las reglas del bot."""
        return abrir_planilla_out(await planillas.open_or_create(ctx, body.fecha, body.hoja))

    @router.get("/{planilla_id}", response_model=PlanillaOut)
    async def detail(planilla_id: str, ctx: BusinessContext = Depends(current)):
        return planilla_out(await asyncio.to_thread(planillas.detail, ctx.business, planilla_id))

    @router.get("/{planilla_id}/resumen", response_model=ResumenOut)
    async def overview(planilla_id: str, ctx: BusinessContext = Depends(current)):
        """Totales y cuántas filas lleva cada sección."""
        return resumen_out(await asyncio.to_thread(planillas.overview, ctx.business, planilla_id))

    return router
