"""Vinculación de la app y manejo de sesiones (públicos: no piden token)."""
import asyncio

from fastapi import APIRouter, Request, Response

from mobile.auth import AppAuthService
from mobile.dto import (
    EstadoVinculacionOut,
    RefreshRequest,
    SesionOut,
    VinculacionOut,
    VinculacionRequest,
    estado_vinculacion_out,
    sesion_out,
    vinculacion_out,
)
from mobile.errors import TooManyRequests
from mobile.profile_service import ProfileService
from mobile.security import SlidingWindowLimiter


def create_auth_router(
    auth: AppAuthService, profiles: ProfileService, limiter: SlidingWindowLimiter
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["App · Autenticación"])

    @router.post("/vinculaciones", response_model=VinculacionOut, status_code=201)
    async def start_pairing(request: Request, body: VinculacionRequest | None = None):
        """Crea un código para enviar al bot por WhatsApp ("VINCULAR 482913")."""
        client = request.client.host if request.client else "?"
        if not limiter.allow(client):
            raise TooManyRequests(
                "Pediste demasiados códigos. Espera unos minutos e intenta de nuevo.",
                "DEMASIADAS_VINCULACIONES",
            )
        start = await asyncio.to_thread(auth.start_pairing, body.dispositivo if body else None)
        return vinculacion_out(start)

    @router.get("/vinculaciones/{vinculacion_id}", response_model=EstadoVinculacionOut)
    async def poll_pairing(vinculacion_id: str):
        """La app consulta cada pocos segundos. Al confirmarse entrega la sesión UNA vez."""
        poll = await asyncio.to_thread(auth.poll_pairing, vinculacion_id)
        profile = None
        if poll.session is not None:
            profile = await asyncio.to_thread(profiles.profile, poll.session.context)
        return estado_vinculacion_out(poll, profile)

    @router.post("/refresh", response_model=SesionOut)
    async def refresh(body: RefreshRequest):
        """Cambia el refresh token por uno nuevo (el anterior deja de servir)."""
        issued = await asyncio.to_thread(auth.refresh, body.refresh_token)
        profile = await asyncio.to_thread(profiles.profile, issued.context)
        return sesion_out(issued, profile)

    @router.post("/logout", status_code=204)
    async def logout(body: RefreshRequest):
        """Cierra la sesión de este dispositivo. Siempre responde 204."""
        await asyncio.to_thread(auth.logout, body.refresh_token)
        return Response(status_code=204)

    return router
