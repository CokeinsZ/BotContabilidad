from fastapi import APIRouter, Request

from whatsapp.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/whatsapp", tags=["Whatsapp"])
service = None

def init_service(dispatcher):
    global service
    service = WhatsAppService(dispatcher=dispatcher)

@router.post("/messages-upsert")
async def read_messages(request: Request):
    try:
        body = await request.json()
        await service.handle_incoming_message(body)
        return {"status": "received"}
    except Exception as e:
        return {"status": "error", "message": str(e)}