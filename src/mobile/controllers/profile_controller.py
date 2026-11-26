"""Perfil del administrador y su negocio."""
import asyncio

from fastapi import APIRouter, Depends

from database.models import BusinessContext
from mobile.dto import NombreRequest, PerfilOut, perfil_out
from mobile.profile_service import ProfileService
from mobile.security.dependencies import CurrentContext


def create_profile_router(profiles: ProfileService, current: CurrentContext) -> APIRouter:
    router = APIRouter(tags=["App · Perfil"])

    @router.get("/perfil", response_model=PerfilOut)
    async def get_profile(ctx: BusinessContext = Depends(current)):
        return perfil_out(await asyncio.to_thread(profiles.profile, ctx))

    @router.patch("/negocio", response_model=PerfilOut)
    async def rename_business(body: NombreRequest, ctx: BusinessContext = Depends(current)):
        """Se usa en las planillas nuevas; las existentes no cambian."""
        return perfil_out(await asyncio.to_thread(profiles.rename_business, ctx, body.nombre))

    @router.patch("/administrador", response_model=PerfilOut)
    async def rename_administrator(body: NombreRequest, ctx: BusinessContext = Depends(current)):
        """Se usa en las planillas nuevas; las existentes no cambian."""
        return perfil_out(await asyncio.to_thread(profiles.rename_administrator, ctx, body.nombre))

    return router
