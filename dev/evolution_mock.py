"""Evolution API simulada para pruebas locales.

Recibe lo que el bot "envía por WhatsApp" y lo guarda en memoria para que
`dev/send.py` lo muestre. También sirve audios registrados previamente
(endpoint `getBase64FromMediaMessage`) para probar el flujo de voz.

    GET    /messages?since=<id>   -> mensajes enviados por el bot
    PUT    /media/{message_id}    -> registra un audio en base64 ({"base64": ...})
"""
from fastapi import FastAPI, Request

app = FastAPI(title="Evolution API (simulada)")

MESSAGES: list[dict] = []
MEDIA: dict[str, str] = {}


@app.post("/message/sendText/{instance}")
async def send_text(instance: str, request: Request):
    body = await request.json()
    message = {"id": len(MESSAGES) + 1, "instance": instance, "to": body.get("number"), "text": body.get("text")}
    MESSAGES.append(message)
    print(f"[WhatsApp -> {message['to']}] {message['text']}", flush=True)
    return {"key": {"id": f"mock-{message['id']}"}, "status": "PENDING"}


@app.get("/messages")
async def list_messages(since: int = 0):
    return [m for m in MESSAGES if m["id"] > since]


@app.put("/media/{message_id}")
async def put_media(message_id: str, request: Request):
    MEDIA[message_id] = (await request.json())["base64"]
    return {"status": "ok"}


@app.post("/chat/getBase64FromMediaMessage/{instance}")
async def get_media(instance: str, request: Request):
    body = await request.json()
    message_id = body.get("message", {}).get("key", {}).get("id", "")
    return {"base64": MEDIA.get(message_id)}
