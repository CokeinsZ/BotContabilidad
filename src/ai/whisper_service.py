"""Servicio de transcripción de audio usando Whisper."""
import httpx

from config.log import log_error


class WhisperService:
    """Transcribe audios a texto mediante una instancia externa de Whisper."""

    def __init__(self, whisper_url: str):
        self._whisper_url = whisper_url
        self._client = httpx.AsyncClient()

    async def transcribe_audio(self, audio_binary: bytes) -> str | None:
        """Transcribe un audio en formato binario (ogg) a texto."""
        try:
            files = {"audio_file": ("audio.ogg", audio_binary, "audio/ogg")}
            headers = {"accept": "application/json"}

            response = await self._client.post(
                self._whisper_url,
                files=files,
                headers=headers,
                timeout=None,
            )
            response.raise_for_status()
            return response.json().get("text")

        except httpx.HTTPStatusError as error:
            log_error(
                "transcribiendo audio en Whisper",
                error,
                f"status={error.response.status_code} body={error.response.text[:1000]!r}",
            )
        except Exception as error:
            log_error("transcribiendo audio en Whisper (inesperado)", error)
        return None
