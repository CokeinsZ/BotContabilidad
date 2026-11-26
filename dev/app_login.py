"""Vincula la "app" contra el bot local y muestra los tokens, sin teléfono.

Hace lo mismo que la app móvil: pide un código, lo envía al bot como si
fuera un mensaje de WhatsApp del administrador ("VINCULAR 482913") y
consulta hasta recibir la sesión.

Requiere el entorno local levantado (`docker compose -f docker-compose.local.yml up`)
y APP_JWT_SECRET en el .env.

    uv run python dev/app_login.py
    uv run python dev/app_login.py --phone 998

Luego, por ejemplo:

    curl -H "Authorization: Bearer <access_token>" http://localhost:8000/app/perfil
"""
import argparse
import sys
import time
import uuid

import httpx

BOT_URL = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phone", default="999", help="Teléfono/identificador del administrador")
    parser.add_argument("--bot", default=BOT_URL)
    args = parser.parse_args()

    start = httpx.post(f"{args.bot}/app/auth/vinculaciones", json={"dispositivo": "dev/app_login.py"})
    if start.status_code != 201:
        print(f"⚠️ No se pudo crear la vinculación: {start.status_code} {start.text}", file=sys.stderr)
        return 1
    pairing = start.json()
    print(f"Código: {pairing['codigo']}  (mensaje: {pairing['mensaje']})")

    webhook = {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": f"{args.phone}@s.whatsapp.net", "fromMe": False, "id": uuid.uuid4().hex.upper()},
            "messageType": "conversation",
            "message": {"conversation": pairing["mensaje"]},
        },
    }
    httpx.post(f"{args.bot}/whatsapp/messages-upsert", json=webhook, timeout=30).raise_for_status()

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        poll = httpx.get(f"{args.bot}/app/auth/vinculaciones/{pairing['vinculacion_id']}").json()
        if poll["estado"] == "confirmada":
            session = poll["sesion"]
            profile = session["perfil"]
            print(f"✅ Vinculada: {profile['administrador']['nombre']} · {profile['negocio']['nombre']}\n")
            print(f"access_token  = {session['access_token']}")
            print(f"refresh_token = {session['refresh_token']}")
            return 0
        if poll["estado"] != "pendiente":
            print(f"⚠️ La vinculación quedó '{poll['estado']}'. ¿El teléfono está registrado?", file=sys.stderr)
            return 1
        time.sleep(0.5)
    print("⚠️ El bot no confirmó la vinculación a tiempo.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
