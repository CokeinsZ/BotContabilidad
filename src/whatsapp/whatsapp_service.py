import os
import base64
import httpx
from dotenv import load_dotenv

class WhatsAppService:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("EVOLUTION_API_BASE_URL")
        self.whisper_url = os.getenv("WHISPER_URL")
        self.instance_name = os.getenv("EVOLUTION_API_INSTANCE_NAME")
        self.token = os.getenv("EVOLUTION_API_TOKEN")
        self.client = httpx.AsyncClient()

    def handle_incoming_message(self, body):
        """

        Args:
            body: El cuerpo del mensaje entrante.
        """

        if (body.get("data", {}).get("messageType") == "audioMessage"):
            message_id = body.get('data', {}).get('key', {}).get('id')
            return self._process_audio_message(message_id)
        else:
            return self._process_text_message(body)
        
    def _process_audio_message(self, message_id):
        """
        Procesa un mensaje de audio entrante.

        Args:
            message_id: El ID del mensaje de audio.
        """
        audio_binary = None
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
            
            response = httpx.post(
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
            audio_binary = base64.b64decode(base64_audio)            
        except httpx.HTTPError as e:
            print(f"Error al obtener audio: {e}")
        except Exception as e:
            print(f"Error procesando audio: {e}")

        self.transcribe_audio(audio_binary)

    def transcribe_audio(self, audio_binary):
        """
        Transcribe el audio utilizando whisper.
        Args:
            audio_binary: El audio en formato binario.
        """
        try:
            files = {
                'audio_file': ('audio.ogg', audio_binary, 'audio/ogg')
            }

            headers = {'accept': 'application/json'}
            
            response = httpx.post(
                self.whisper_url,
                files=files,
                headers=headers,
                timeout=None
            )
            
            response.raise_for_status()
            
            transcription = response.json().get("text")
            print(f"Transcription: {transcription}")
            return transcription
            
        except httpx.HTTPStatusError as e:
            print(f"Error de la API ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def _process_text_message(self, body):
        """
        Procesa un mensaje de texto entrante.

        Args:
            body: El cuerpo del mensaje entrante.
        """
        print(body)
        