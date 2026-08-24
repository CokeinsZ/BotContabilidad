"""Servicio de WhatsApp: recepción y envío de mensajes vía Evolution API."""
import asyncio
import base64

import httpx

from accounting.accounting_service import AccountingService
from ai.deepseek_service import DeepSeekService
from ai.whisper_service import WhisperService
from whatsapp.dto import IncomingMessage


class WhatsAppService:
    """Orquesta el flujo: mensaje -> (audio->texto) -> comando -> respuesta."""

    def __init__(
        self,
        evolution_base_url: str,
        evolution_instance_name: str,
        evolution_token: str,
        whisper_service: WhisperService,
        deepseek_service: DeepSeekService,
        accounting_service: AccountingService,
    ):
        self._base_url = evolution_base_url
        self._instance_name = evolution_instance_name
        self._token = evolution_token
        self._client = httpx.AsyncClient()

        self._whisper = whisper_service
        self._deepseek = deepseek_service
        self._accounting = accounting_service

    async def handle_incoming_message(self, body: dict) -> None:
        """Procesa un webhook `messages-upsert` de Evolution API."""
        message = IncomingMessage.from_webhook(body)

        # Solo chats individuales (se ignoran grupos, estados, canales, etc.).
        if not message.is_individual_chat:
            return

        if message.is_audio:
            command = await self._audio_to_command(message.key.id)
        else:
            command = await self._text_to_command(message.text)

        if not command:
            return

        # Las llamadas a Google son síncronas: se ejecutan en un hilo aparte
        # para no bloquear el event loop del servidor.
        response = await asyncio.to_thread(
            self._accounting.handle_command, message.phone_number, command
        )
        if response:
            await self.send_message(message.key.remote_jid, response)

    async def send_message(self, to: str, message: str) -> None:
        """Envía un mensaje de texto a través de Evolution API."""
        try:
            url = f"{self._base_url}/message/sendText/{self._instance_name}"
            payload = {"number": to, "text": message}

            response = await self._client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "apikey": self._token},
            )
            response.raise_for_status()
            print(f"Mensaje enviado a {to}: {message}")

        except httpx.HTTPError as error:
            print(f"Error al enviar mensaje: {error}")
        except Exception as error:
            print(f"Error inesperado al enviar mensaje: {error}")

    # ------------------------------------------------------------------
    # Conversión de entrada a comando
    # ------------------------------------------------------------------
    async def _text_to_command(self, text: str | None) -> str | None:
        if not text:
            return None
        return await self._deepseek.extract_commands(text)

    async def _audio_to_command(self, message_id: str) -> str | None:
        audio_binary = await self._get_audio_binaries(message_id)
        if not audio_binary:
            return None
        transcription = await self._whisper.transcribe_audio(audio_binary)
        if not transcription:
            return None
        return await self._deepseek.extract_commands(transcription)

    async def _get_audio_binaries(self, message_id: str) -> bytes | None:
        try:
            url = f"{self._base_url}/chat/getBase64FromMediaMessage/{self._instance_name}"
            payload = {
                "message": {"key": {"id": message_id}},
                "convertToMp4": False,
            }

            response = await self._client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json", "apikey": self._token},
            )
            response.raise_for_status()

            base64_audio = response.json().get("base64")
            if not base64_audio:
                print(f"No se obtuvo audio base64 para el mensaje {message_id}")
                return None

            return base64.b64decode(base64_audio)

        except httpx.HTTPError as error:
            print(f"Error al obtener audio: {error}")
        except Exception as error:
            print(f"Error procesando audio: {error}")
        return None
