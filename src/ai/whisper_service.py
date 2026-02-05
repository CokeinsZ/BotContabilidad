import httpx

from config import WHISPER_URL

class WhisperService:
    def __init__(self):
        self.whisper_url = WHISPER_URL
        self.client = httpx.AsyncClient()

    async def transcribe_audio(self, audio_binary):
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
            
            response = await self.client.post(
                self.whisper_url,
                files=files,
                headers=headers,
                timeout=None
            )
            
            response.raise_for_status()
            
            transcription = response.json().get("text")
            return transcription
            
        except httpx.HTTPStatusError as e:
            print(f"Error de la API ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            print(f"Unexpected error: {e}")
