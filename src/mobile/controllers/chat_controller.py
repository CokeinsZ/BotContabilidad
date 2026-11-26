"""Chat de una planilla: enviar, estado, responder y cancelar la pregunta pendiente.

El historial no se guarda en el servidor: la app lo guarda en el teléfono.
"""
from fastapi import APIRouter, Depends

from database.models import BusinessContext
from mobile.chat import ChatService
from mobile.dto import (
    EstadoChatOut,
    MensajeRequest,
    ResultadoChatOut,
    SeleccionRequest,
    estado_chat_out,
    resultado_chat_out,
)
from mobile.security.dependencies import CurrentContext


def create_chat_router(chat: ChatService, current: CurrentContext) -> APIRouter:
    router = APIRouter(prefix="/planillas/{planilla_id}", tags=["App · Chat"])

    @router.get("/estado", response_model=EstadoChatOut)
    async def state(planilla_id: str, ctx: BusinessContext = Depends(current)):
        """Pregunta pendiente y qué revertiría 'deshacer' (al abrir el chat)."""
        return estado_chat_out(await chat.state(ctx, planilla_id))

    @router.post("/mensajes", response_model=ResultadoChatOut)
    async def send(planilla_id: str, body: MensajeRequest, ctx: BusinessContext = Depends(current)):
        """Ejecuta el mensaje en esta planilla. Reenviar el mismo client_id no duplica nada."""
        result = await chat.send(ctx, planilla_id, body.client_id, body.comando, body.texto)
        return resultado_chat_out(result)

    @router.post("/seleccion", response_model=ResultadoChatOut)
    async def answer(planilla_id: str, body: SeleccionRequest, ctx: BusinessContext = Depends(current)):
        """Responde la pregunta pendiente con el número de la opción."""
        return resultado_chat_out(await chat.answer(ctx, planilla_id, body.opcion))

    @router.delete("/seleccion", response_model=ResultadoChatOut)
    async def cancel(planilla_id: str, ctx: BusinessContext = Depends(current)):
        """Cancela la pregunta pendiente: el comando que preguntó se borra de la planilla."""
        return resultado_chat_out(await chat.cancel(ctx, planilla_id))

    return router
