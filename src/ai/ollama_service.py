import httpx

from config import OLLAMA_URL, OLLAMA_MODEL

class OllamaService:
    def __init__(self):
        self.client = httpx.AsyncClient()
        self.ollama_url = OLLAMA_URL
        self.ollama_model = OLLAMA_MODEL

    async def extract_commands(self, audio_transcription):
        """
        Traduce el lenguaje natural de la transcripción a comandos del Bot de Contabilidad.
        """
        prompt = f"""
            Eres un traductor de lenguaje natural a comandos técnicos para un Bot de Contabilidad.
            Tu objetivo es transformar lo que el usuario dice en uno de los siguientes comandos válidos:

            COMANDOS VÁLIDOS:
            1. hoja <fecha> (ej: hoja 25-01-2026)
            2. gasto <monto> <descripcion> (ej: gasto 5000 papas amarillas)
            3. trabajador <monto> <nombre> (ej: trabajador 50000 juan panadero)
            4. administrador <monto> (ej: administrador 20000)
            5. retiro <monto> <descripcion> (ej: retiro 100000 Postobón)
            6. saldo <monto> (ej: saldo 450000)
            7. efectivo <monto> (ej: efectivo 800000)
            8. terminar_dia
            9. instrucciones
            10. deshacer

            REGLAS ESTRICTAS:
            - Si el usuario dice "lucas", "mil" o "k", conviértelo a números (ej: "5 lucas" -> 5000, "20 mil" -> 20000).
            - Solo responde con el comando. No digas "Aquí tienes", ni uses puntos finales.
            - Si no entiendes la intención, responde exactamente: instrucciones

            
            El usuario dijo: "{audio_transcription}"
        """
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                }
            }

            response = await self.client.post(
                self.ollama_url,
                json=payload,
                timeout=None
            )

            response.raise_for_status()
            return response.json().get("response").strip().lower()

        except httpx.HTTPStatusError as e:
            print(f"Error de la API ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            print(f"Unexpected error: {e}")