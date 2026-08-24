"""Endpoints HTTP del módulo de WhatsApp (webhook de Evolution API)."""
from fastapi import APIRouter, Request

from whatsapp.whatsapp_service import WhatsAppService


def create_whatsapp_router(service: WhatsAppService) -> APIRouter:
    """Factory del router de WhatsApp (inyección de dependencias)."""
    router = APIRouter(prefix="/whatsapp", tags=["Whatsapp"])

    @router.post("/messages-upsert")
    async def read_messages(request: Request):
        try:
            body = await request.json()
            await service.handle_incoming_message(body)
            return {"status": "received"}
        except Exception as error:
            # Dejar rastro en los logs: Evolution reintenta o descarta según
            # el código, pero sin este print el fallo era invisible.
            print(f"Error procesando mensaje entrante: {error}")
            return {"status": "error", "message": str(error)}

    return router
