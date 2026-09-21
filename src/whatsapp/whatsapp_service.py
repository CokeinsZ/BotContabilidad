"""Servicio de WhatsApp: recepción y envío de mensajes vía Evolution API."""
import asyncio
import base64

import httpx

from accounting.accounting_service import AccountingService
from ai.deepseek_service import DeepSeekService
from ai.whisper_service import WhisperService
from config.log import log_error, log_warning
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

        reason = message.ignore_reason
        if reason:
            print(f"Mensaje ignorado: {reason}")
            return

        print(
            f"Mensaje recibido de {message.phone_number} "
            f"({'audio' if message.is_audio else 'texto'})"
        )

        if message.is_audio:
            try:
                command = await self._audio_to_command(message.key.id)
            except Exception as error:
                log_error(
                    "convirtiendo audio a comando",
                    error,
                    f"phone={message.phone_number} message_id={message.key.id}",
                )
                return
        else:
            try:
                command = await self._text_to_command(message.text, message.phone_number)
            except Exception as error:
                log_error(
                    "convirtiendo texto a comando (DeepSeek)",
                    error,
                    f"phone={message.phone_number} text={message.text!r}",
                )
                return

        if not command:
            print(f"No se pudo extraer un comando del mensaje de {message.phone_number}")
            return

        print(f"Comando extraído: '{command}' (de {message.phone_number})")

        # Las llamadas a Google son síncronas: se ejecutan en un hilo aparte
        # para no bloquear el event loop del servidor.
        try:
            responses = await asyncio.to_thread(
                self._accounting.handle_command, message.phone_number, command
            )
        except Exception as error:
            log_error(
                "procesando comando de WhatsApp",
                error,
                f"phone={message.phone_number} command={command!r} "
                f"remote_jid={message.key.remote_jid}",
            )
            await self.send_message(
                message.key.remote_jid,
                "⚠️ Ocurrió un error interno al procesar tu mensaje. "
                "Revisa los logs del servidor para el detalle.",
            )
            return
        for response in responses:
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
            log_error("enviando mensaje de WhatsApp", error, f"to={to} text={message!r}")
        except Exception as error:
            log_error(
                "enviando mensaje de WhatsApp (inesperado)", error, f"to={to} text={message!r}"
            )

    # ------------------------------------------------------------------
    # Conversión de entrada a comando
    # ------------------------------------------------------------------
    async def _text_to_command(self, text: str | None, phone_number: str) -> str | None:
        if not text:
            return None
        # Si el usuario está respondiendo una selección pendiente con un
        # número, NO pasar por la IA: el número es la respuesta directa.
        if text.strip().isdigit() and await asyncio.to_thread(
            self._accounting.has_pending_selection, phone_number
        ):
            return text.strip()
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
                log_warning(
                    "audio sin contenido base64",
                    f"message_id={message_id} response={response.text[:500]!r}",
                )
                return None

            return base64.b64decode(base64_audio)

        except httpx.HTTPError as error:
            log_error("obteniendo audio de Evolution", error, f"message_id={message_id}")
        except Exception as error:
            log_error("procesando audio (inesperado)", error, f"message_id={message_id}")
        return None
