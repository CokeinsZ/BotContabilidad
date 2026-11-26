"""Servicio de WhatsApp: recepción y envío de mensajes vía Evolution API.

El webhook responde a Evolution de inmediato (`accept`) y el mensaje se
procesa en segundo plano: así Evolution nunca espera (DeepSeek + Google
pueden tardar, sobre todo si la cuota de Google obliga a reintentar) y no
reenvía el mismo mensaje. Además:

- Los mensajes de un mismo remitente se procesan en orden de llegada (un
  "1" que responde un menú no puede adelantarse al mensaje que lo creó).
- Un mensaje con un id ya recibido se descarta (reenvíos de Evolution).
- "VINCULAR <código>" y "cerrar app" son para la app móvil: se responden sin
  pasar por DeepSeek ni por la contabilidad (no cancelan un menú pendiente).
"""
import asyncio
import base64
from collections import OrderedDict
from typing import TYPE_CHECKING

import httpx

from accounting.accounting_service import AccountingService
from ai.deepseek_service import DeepSeekService
from ai.whisper_service import WhisperService
from config.log import log_error, log_warning
from whatsapp.dto import IncomingMessage

if TYPE_CHECKING:
    from mobile.auth import AppAuthService

#: Cuántos ids de mensaje se recuerdan para descartar duplicados.
SEEN_MESSAGES_LIMIT = 5000

PROCESSING = "processing"
DONE = "done"
UNKNOWN = "unknown"


class WhatsAppService:
    """Orquesta el flujo: mensaje -> (audio->texto) -> comandos -> respuestas."""

    def __init__(
        self,
        evolution_base_url: str,
        evolution_instance_name: str,
        evolution_token: str,
        whisper_service: WhisperService,
        deepseek_service: DeepSeekService,
        accounting_service: AccountingService,
        app_auth: "AppAuthService | None" = None,
    ):
        self._base_url = evolution_base_url
        self._instance_name = evolution_instance_name
        self._token = evolution_token
        self._client = httpx.AsyncClient()

        self._whisper = whisper_service
        self._deepseek = deepseek_service
        self._accounting = accounting_service
        self._app_auth = app_auth

        self._tasks: set[asyncio.Task] = set()
        self._sender_locks: dict[str, asyncio.Lock] = {}
        self._messages: OrderedDict[str, str] = OrderedDict()   # id -> estado

    # ------------------------------------------------------------------
    # Recepción (webhook)
    # ------------------------------------------------------------------
    def accept(self, body: dict) -> str:
        """Registra el webhook y agenda su procesamiento. No espera nada.

        Devuelve "received", "duplicate" o "ignored".
        """
        message = IncomingMessage.from_webhook(body)
        reason = message.ignore_reason
        if reason:
            print(f"Mensaje ignorado: {reason}")
            return "ignored"
        message_id = message.key.id
        if message_id:
            if message_id in self._messages:
                print(f"Mensaje duplicado ignorado: id={message_id}")
                return "duplicate"
            self._remember(message_id, PROCESSING)

        task = asyncio.create_task(self._process_in_order(message, message_id))
        self._tasks.add(task)                    # evita que el GC cancele la tarea
        task.add_done_callback(self._tasks.discard)
        return "received"

    def status(self, message_id: str) -> str:
        """Estado del procesamiento de un mensaje: processing / done / unknown."""
        return self._messages.get(message_id, UNKNOWN)

    async def wait_idle(self) -> None:
        """Espera a que terminen los mensajes en curso (pruebas / apagado)."""
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    def _remember(self, message_id: str, state: str) -> None:
        self._messages[message_id] = state
        self._messages.move_to_end(message_id)
        while len(self._messages) > SEEN_MESSAGES_LIMIT:
            self._messages.popitem(last=False)

    async def _process_in_order(self, message: IncomingMessage, message_id: str) -> None:
        sender = message.key.remote_jid or message.phone_number
        lock = self._sender_locks.setdefault(sender, asyncio.Lock())
        try:
            async with lock:   # FIFO: los mensajes de un remitente, en orden
                await self.handle_incoming_message(message)
        except Exception as error:
            log_error(
                "procesando mensaje de WhatsApp en segundo plano",
                error,
                f"message_id={message_id} remote_jid={message.key.remote_jid}",
            )
        finally:
            if message_id:
                self._remember(message_id, DONE)

    # ------------------------------------------------------------------
    # Procesamiento
    # ------------------------------------------------------------------
    async def handle_incoming_message(self, message: IncomingMessage) -> None:
        """Procesa un mensaje completo y envía las respuestas."""
        reason = message.ignore_reason
        if reason:
            print(f"Mensaje ignorado: {reason}")
            return

        print(
            f"Mensaje recibido de {message.phone_number} "
            f"({'audio' if message.is_audio else 'texto'})"
        )

        if not message.is_audio and await self._answer_app_message(message):
            return

        if message.is_audio:
            try:
                commands = await self._audio_to_commands(message.key.id)
            except Exception as error:
                log_error(
                    "convirtiendo audio a comandos",
                    error,
                    f"phone={message.phone_number} message_id={message.key.id}",
                )
                return
        else:
            try:
                commands = await self._text_to_commands(message.text, message.phone_number)
            except Exception as error:
                log_error(
                    "convirtiendo texto a comandos (DeepSeek)",
                    error,
                    f"phone={message.phone_number} text={message.text!r}",
                )
                return

        if commands is None:
            print(f"No se pudo procesar el mensaje de {message.phone_number}")
            return

        print(f"Comandos extraídos: {commands} (de {message.phone_number})")

        # Las llamadas a Google son síncronas: se ejecutan en un hilo aparte
        # para no bloquear el event loop del servidor. Aunque no haya
        # comandos se llama igual: un mensaje cualquiera cancela los menús
        # pendientes, y el servicio responde la ayuda corta.
        try:
            responses = await asyncio.to_thread(
                self._accounting.handle_commands, message.phone_number, commands
            )
        except Exception as error:
            log_error(
                "procesando comandos de WhatsApp",
                error,
                f"phone={message.phone_number} commands={commands!r} "
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

    async def _answer_app_message(self, message: IncomingMessage) -> bool:
        """Responde "VINCULAR <código>" / "cerrar app". True si el mensaje era para la app."""
        if self._app_auth is None or not self._app_auth.is_app_message(message.text):
            return False
        try:
            reply = await asyncio.to_thread(
                self._app_auth.handle_whatsapp_text, message.phone_number, message.text
            )
        except Exception as error:
            log_error(
                "procesando mensaje de vinculación de la app",
                error,
                f"phone={message.phone_number} text={message.text!r}",
            )
            reply = "⚠️ No se pudo procesar el mensaje de la app. Intenta de nuevo."
        if reply:
            await self.send_message(message.key.remote_jid, reply)
        return True

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
    # Conversión de entrada a comandos
    # ------------------------------------------------------------------
    async def _text_to_commands(self, text: str | None, phone_number: str) -> list[str] | None:
        if not text:
            return None
        # Si el usuario está respondiendo una selección pendiente con un
        # número, NO pasar por la IA: el número es la respuesta directa.
        if text.strip().isdigit() and await asyncio.to_thread(
            self._accounting.has_pending_selection, phone_number
        ):
            return [text.strip()]
        return await self._deepseek.extract_commands(text)

    async def _audio_to_commands(self, message_id: str) -> list[str] | None:
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
