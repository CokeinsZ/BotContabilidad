"""Servicio de extracción de comandos desde lenguaje natural usando DeepSeek."""
import asyncio
from datetime import datetime

from openai import OpenAI


class DeepSeekService:
    """Convierte texto en lenguaje natural a comandos del bot."""

    def __init__(self, api_url: str, api_key: str):
        self._client = OpenAI(api_key=api_key, base_url=api_url)

    async def extract_commands(self, text: str) -> str:
        """Extrae el comando del bot a partir de un mensaje en lenguaje natural."""
        fecha_hoy = datetime.now().strftime("%d-%m-%Y")
        prompt = f"""
            Eres un conversor de audio a comandos de texto. Tu salida debe ser ÚNICAMENTE el comando.
            NO respondas con "Aquí tienes", NO uses "Comando:", NO uses negritas, NO uses puntos finales.

            FECHA DE HOY: {fecha_hoy}

            DICCIONARIO DE COMANDOS (incluye atajos):
            - "hoja <dd-mm-aaaa>" (alias: "h") -> Para crear o seleccionar planilla.
            - "gasto <monto> <descripción>" (alias: "g") -> Para compras de insumos/mercancía.
            - "limpieza <monto>" (alias: "aseo", "l") -> Para gastos de productos de aseo/limpieza.
            - "alimentacion <monto>" (alias: "comida", "a") -> Para gastos de alimentación/comida del personal.
            - "trabajador <monto> <nombre>" (alias: "t", "trabajadores") -> Para pagar sueldos o adelantos a personas. Puede que el usuario no indique el nombre en ese caso el nombre será "Turno". El usuario tambie puede que indique el tipo de pago (ej: "cosina", "vale") en ese caso al nombre une el tipo de pago.
            - "administrador <monto>" (alias: "admin") -> Vales para el jefe/dueño.
            - "retiro <monto> <descripción>" (alias: "r") -> Sacar dinero de la caja.
            - "saldo <monto>" (alias: "s") -> Informar cuánto dinero físico hay.
            - "efectivo <monto>" (alias: "e") -> Dinero de ventas del día.
            - "inversion <monto> <descripción>" (alias: "inversiones", "inv") -> Para registrar inversiones en el negocio.
            - "terminar_dia" (alias: "resumen") -> Finalizar el día y obtener resumen.
            - "instrucciones" (alias: "i", "help") -> Mostrar instrucciones y ayuda de uso.
            - "deshacer" (alias: "undo") -> Deshacer el último comando ejecutado.

            REGLAS DE ORO:
            1. Si hay un NOMBRE de persona (ej: Julian, Maria, Stiven), usa 'trabajador', NO 'gasto'.
            2. Convierte "lucas", "mil", "k" en ceros (ej: 5 lucas = 5000).
            3. Convierte "millones", "millón", "melones" en seis ceros (ej: 2 millones = 2000000).
            4. Los alias puede que los use el usuario pero tu SOLO usas el comando principal.
            5. Si el usuario especificamente dice gasto, respeta su decisión y ponlo como un gasto normal, no lo interpretes como aseo o comida o pago a trabajador, esos tienen su propio comando.
            6. Si el usuario dice "hoy", usa {fecha_hoy}.
            7. Responde SOLO el comando.

            EJEMPLOS:
            Usuario: "Pon la hoja de hoy" -> hoja {fecha_hoy}
            Usuario: "Pagale 40 lucas a Julian" -> trabajador 40000 julian
            Usuario: "Trabajador 20000 Mari cosina" -> trabajador 20000 mari cocina
            Usuario: "Vendí 150k en efectivo" -> efectivo 150000
            Usuario: "Le di un vale de 20k al administrador" -> administrador 20000
            Usuario: "Compré azúcar por 60 mil" -> gasto 60000 azúcar
            Usuario: "Retiro de 100k para el banco" -> retiro 100000 banco
            Usuario: "Retiro de 1 millon 300 para Levapan" -> retiro 1300000 levapan
            Usuario: "Compré jabón y escobas por 25 lucas" -> limpieza 25000
            Usuario: "Gasto de aseo 15 mil" -> limpieza 15000
            Usuario: "Almuerzo para los trabajadores 30k" -> alimentacion 30000
            Usuario: "Comida del personal 20 lucas" -> alimentacion 20000
            Usuario: "Inversión de 500k en maquinaria" -> inversion 500000 maquinaria


            Con esa información, convierte las transcripciones en un comando
        """

        # El SDK de OpenAI es síncrono: se ejecuta en un hilo aparte para
        # no bloquear el event loop mientras se espera la respuesta.
        response = await asyncio.to_thread(
            self._client.chat.completions.create,
            model="deepseek-chat",
            temperature=0,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            stream=False,
        )

        return response.choices[0].message.content.strip().lower()
