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

        from datetime import datetime
        fecha_hoy = datetime.now().strftime("%d-%m-%Y")

        prompt = f"""
            Eres un conversor de audio a comandos de texto. Tu salida debe ser ÚNICAMENTE el comando. 
            NO respondas con "Aquí tienes", NO uses "Comando:", NO uses negritas, NO uses puntos finales.

            FECHA DE HOY: {fecha_hoy}

            DICCIONARIO DE COMANDOS:
            - "hoja <dd-mm-aaaa>" -> Para crear o seleccionar planilla.
            - "gasto <monto> <descripción>" -> Para compras de insumos/mercancía.
            - "trabajador <monto> <nombre>" -> Para pagar sueldos o adelantos a personas.
            - "administrador <monto>" -> Vales para el jefe/dueño.
            - "retiro <monto> <descripción>" -> Sacar dinero de la caja.
            - "saldo <monto>" -> Informar cuánto dinero físico hay.
            - "efectivo <monto>" -> Dinero de ventas del día.
            - "terminar_dia", "instrucciones", "deshacer".

            REGLAS DE ORO:
            1. Si hay un NOMBRE de persona (ej: Julian, Maria, Stiven), usa 'trabajador', NO 'gasto'.
            2. Convierte "lucas", "mil", "k" en ceros (ej: 5 lucas = 5000).
            3. Si el usuario dice "hoy", usa {fecha_hoy}.
            4. Responde SOLO el comando.

            EJEMPLOS:
            Usuario: "Pon la hoja de hoy" -> hoja {fecha_hoy}
            Usuario: "Pagale 40 lucas a Julian" -> trabajador 40000 julian
            Usuario: "Le di un vale de 20k al administrador" -> administrador 20000
            Usuario: "Compré azúcar por 60 mil" -> gasto 60000 azúcar
            Usuario: "Retiro de 100k para el banco" -> retiro 100000 banco

            
            Con esa información, convierte esta transcripción en un comando: 
            {audio_transcription}
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