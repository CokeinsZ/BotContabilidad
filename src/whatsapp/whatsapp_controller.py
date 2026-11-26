"""Endpoints HTTP del módulo de WhatsApp (webhook de Evolution API)."""
from fastapi import APIRouter, Request

from config.log import log_error
from whatsapp.whatsapp_service import WhatsAppService


def create_whatsapp_router(service: WhatsAppService) -> APIRouter:
    """Factory del router de WhatsApp (inyección de dependencias)."""
    router = APIRouter(prefix="/whatsapp", tags=["Whatsapp"])

    @router.post("/messages-upsert")
    async def read_messages(request: Request):
        """Responde 200 de inmediato; el mensaje se procesa en segundo plano."""
        body = None
        try:
            body = await request.json()
            return {"status": service.accept(body)}
        except Exception as error:
            # Dejar rastro en los logs con el body parcial para poder reproducir.
            try:
                preview = str(body)[:2000] if body is not None else "<sin body>"
            except Exception:
                preview = "<body no serializable>"
            log_error("recibiendo webhook messages-upsert", error, f"body={preview}")
            return {"status": "error", "message": str(error)}

    @router.get("/messages/{message_id}/status")
    async def message_status(message_id: str):
        """Estado del procesamiento de un mensaje: processing / done / unknown."""
        return {"status": service.status(message_id)}

    return router
