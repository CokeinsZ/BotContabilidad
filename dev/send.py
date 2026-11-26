"""Envía un mensaje de WhatsApp simulado al bot local y muestra las respuestas.

Requiere el entorno local levantado (`docker compose -f docker-compose.local.yml up`).

    uv run python dev/send.py "gasto 5000 pan y 3000 leche"
    uv run python dev/send.py --phone 998 "deshacer"
    uv run python dev/send.py --audio nota.ogg

El teléfono por defecto (999) es el administrador del business de pruebas.
"""
import argparse
import base64
import sys
import uuid
from pathlib import Path

import httpx

BOT_URL = "http://localhost:8000/whatsapp/messages-upsert"
MOCK_URL = "http://localhost:8081"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("text", nargs="?", help="Texto del mensaje")
    parser.add_argument("--phone", default="999", help="Teléfono/identificador del remitente")
    parser.add_argument("--audio", type=Path, help="Archivo de audio (ogg) a enviar como nota de voz")
    parser.add_argument("--bot", default=BOT_URL)
    parser.add_argument("--mock", default=MOCK_URL)
    args = parser.parse_args()
    if not args.text and not args.audio:
        parser.error("indica un texto o --audio")

    message_id = uuid.uuid4().hex.upper()
    key = {"remoteJid": f"{args.phone}@s.whatsapp.net", "fromMe": False, "id": message_id}
    if args.audio:
        audio = base64.b64encode(args.audio.read_bytes()).decode()
        httpx.put(f"{args.mock}/media/{message_id}", json={"base64": audio}).raise_for_status()
        data = {"key": key, "messageType": "audioMessage", "message": {"audioMessage": {}}}
    else:
        data = {"key": key, "messageType": "conversation", "message": {"conversation": args.text}}

    last_id = max((m["id"] for m in httpx.get(f"{args.mock}/messages").json()), default=0)
    # El bot procesa el mensaje completo antes de responder el webhook.
    response = httpx.post(args.bot, json={"event": "messages.upsert", "data": data}, timeout=300)
    response.raise_for_status()
    if response.json().get("status") != "received":
        print(f"⚠️ El webhook respondió: {response.json()}", file=sys.stderr)

    replies = httpx.get(f"{args.mock}/messages", params={"since": last_id}).json()
    if not replies:
        print("(el bot no respondió)")
    for reply in replies:
        print(f"🤖 {reply['text']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
