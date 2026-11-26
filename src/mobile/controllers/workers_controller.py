"""Trabajadores: lista, detalle del período actual y nóminas archivadas."""
import asyncio

from fastapi import APIRouter, Depends

from database.models import BusinessContext
from mobile.dto import (
    NominaDetalleOut,
    TrabajadorDetalleOut,
    TrabajadoresOut,
    nomina_detalle_out,
    trabajador_detalle_out,
    trabajadores_out,
)
from mobile.security.dependencies import CurrentContext
from mobile.workers_service import WorkersService


def create_workers_router(workers: WorkersService, current: CurrentContext) -> APIRouter:
    router = APIRouter(prefix="/trabajadores", tags=["App · Trabajadores"])

    @router.get("", response_model=TrabajadoresOut)
    async def list_workers(ctx: BusinessContext = Depends(current)):
        return trabajadores_out(await asyncio.to_thread(workers.list, ctx.business))

    @router.get("/{trabajador_id}", response_model=TrabajadorDetalleOut)
    async def detail(trabajador_id: str, ctx: BusinessContext = Depends(current)):
        return trabajador_detalle_out(await asyncio.to_thread(workers.detail, ctx.business, trabajador_id))

    @router.get("/{trabajador_id}/nominas/{hoja_id}", response_model=NominaDetalleOut)
    async def archived(trabajador_id: str, hoja_id: int, ctx: BusinessContext = Depends(current)):
        detail = await asyncio.to_thread(workers.archived, ctx.business, trabajador_id, hoja_id)
        return nomina_detalle_out(detail)

    return router
