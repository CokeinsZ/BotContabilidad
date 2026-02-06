import base64
import httpx

from config import EVOLUTION_API_BASE_URL, EVOLUTION_API_INSTANCE_NAME, EVOLUTION_API_TOKEN
from ai.ollama_service import OllamaService
from ai.whisper_service import WhisperService

class WhatsAppService:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        
        self.base_url = EVOLUTION_API_BASE_URL
        self.instance_name = EVOLUTION_API_INSTANCE_NAME
        self.token = EVOLUTION_API_TOKEN
        self.client = httpx.AsyncClient()

        self.whisper_service = WhisperService()
        self.ollama_service = OllamaService()

    async def handle_incoming_message(self, body):
        """

        Args:
            body: El cuerpo del mensaje entrante.
        """

        remote_jid = body.get("data", {}).get("key", {}).get("remoteJid")

        if (body.get("data", {}).get("messageType") == "audioMessage"):
            message_id = body.get('data', {}).get('key', {}).get('id')
            return await self._process_audio_message(message_id, remote_jid)
        else:
            message = body.get("data", {}).get("message", {}).get("conversation")
            return await self._process_text_message(message, remote_jid)
        
    async def send_message(self, to, message):
        """
        Envía un mensaje de texto a través de la API de Evolution.

        Args:
            to: El destinatario del mensaje.
            message: El contenido del mensaje.
        """
        try:
            url = f"{self.base_url}/message/sendText/{self.instance_name}"
            
            payload = {
                "number": to,
                "text": message
            }
            
            response = await self.client.post(
                url,
                json=payload,
                headers = {
                    'Content-Type': 'application/json',
                    'apikey': self.token
                }
            )
            response.raise_for_status()
            print(f"Mensaje enviado a {to}: {message}")
            
        except httpx.HTTPError as e:
            print(f"Error al enviar mensaje: {e}")
        except Exception as e:
            print(f"Error inesperado al enviar mensaje: {e}")

    async def _process_audio_message(self, message_id, remote_jid):
        """
        Procesa un mensaje de audio entrante.

        Args:
            message_id: El ID del mensaje de audio.
            remote_jid: El identificador del remitente.
        """
        audio_binary = await self._get_audio_binaries(message_id)
        audio_transcription = await self.whisper_service.transcribe_audio(audio_binary)
        command = await self.ollama_service.extract_commands(audio_transcription)

        response = self.dispatcher.run(command)
        if response:
            await self.send_message(remote_jid, response)
   
    async def _process_text_message(self, message, remote_jid):
        """
        Procesa un mensaje de texto entrante.

        Args:
            message: El mensaje entrante.
        """
        command = await self.ollama_service.extract_commands(message)

        response = self.dispatcher.run(command)
        if response:
            await self.send_message(remote_jid, response)

    async def _get_audio_binaries(self, message_id):
        try:
            # Obtener el base64 del audio
            url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance_name}"
            
            payload = {
                "message": {
                    "key": {
                        "id": message_id
                    }
                },
                "convertToMp4": False
            }
            
            response = await self.client.post(
                url,
                json=payload,
                headers = {
                    'Content-Type': 'application/json',
                    'apikey': self.token
                }
            )
            response.raise_for_status()
            
            data = response.json()
            base64_audio = data.get("base64")
            
            if not base64_audio:
                print(f"No se obtuvo audio base64 para el mensaje {message_id}")
                return
            
            # Convertir base64 a binario
            return base64.b64decode(base64_audio)            
        except httpx.HTTPError as e:
            print(f"Error al obtener audio: {e}")
        except Exception as e:
            print(f"Error procesando audio: {e}")