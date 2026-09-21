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
            - "segunda planilla" / "tercera planilla" / "2 planilla" / "3 planilla" ... -> Para crear o seleccionar una planilla adicional del mismo día. Si el usuario pide "la segunda planilla", "otra planilla", "una tercera planilla del día", etc., usa este comando con el ordinal correspondiente (palabra o número).
            - "gasto <monto> <descripción>" (alias: "g") -> Para compras de insumos/mercancía.
            - "limpieza <monto>" (alias: "aseo", "l") -> Para gastos de productos de aseo/limpieza.
            - "alimentacion <monto>" (alias: "comida", "a") -> Para gastos de alimentación/comida del personal.
            - "trabajador <monto> <nombre>" (alias: "t", "trabajadores") -> Para registrar préstamos/adelantos a personas (no son pagos de nómina, son préstamos que luego se descuentan). Puede que el usuario no indique el nombre en ese caso el nombre será "Turno". El usuario tambie puede que indique el tipo de pago (ej: "cosina", "vale") en ese caso al nombre une el tipo de pago.
            - "nomina <monto> <nombre>" (alias: "nomina", "n") -> Para registrar pagos de nómina a trabajadores y limpiar sus prestamos. Importante: este comando es diferente al comando "trabajador", el comando "nomina" es para registrar pagos de nómina y el comando "trabajador" es para registrar préstamos.
            - "administrador <monto>" (alias: "admin") -> Vales para el jefe/dueño.
            - "retiro <monto> <descripción>" (alias: "r") -> Sacar dinero de la caja.
            - "saldo <monto>" (alias: "s") -> Informar cuánto dinero físico hay.
            - "efectivo <monto>" (alias: "e") -> Dinero en efectivo de ventas del día.
            - "inversion <monto> <descripción>" (alias: "inversiones", "inv") -> Para registrar inversiones en el negocio.
            - "terminar_dia" (alias: "resumen") -> Finalizar el día y obtener resumen.
            - "instrucciones" (alias: "i", "help") -> Mostrar instrucciones y ayuda de uso.
            - "deshacer" (alias: "undo") -> Deshacer el último comando ejecutado.

            REGLAS DE ORO:
            1. Siempre respeta la decicion del usuario. Si el usuario dice "gasto" el comando es "gasto", no lo interpretes como aseo o comida o pago a trabajador, esos tienen su propio comando.
            2. Siempre respeta la decicion del usuario. Si el usuario dice "retiro" el comando es "retiro", no lo interpretes como gasto, aseo o comida o pago a trabajador, esos tienen su propio comando.
            3. Convierte "lucas", "mil", "k" en tres ceros (ej: 5 lucas = 5000) (ej: 100k = 100000).
            4. Convierte "millones", "millón", "melones" en seis ceros (ej: 2 millones = 2000000).
            5. Los alias puede que los use el usuario pero tu SOLO usas el comando principal.
            6. Si el usuario especificamente dice gasto, respeta su decisión y ponlo como un gasto normal, no lo interpretes como aseo o comida o pago a trabajador, esos tienen su propio comando.
            7. Si el usuario dice "hoy", usa {fecha_hoy}.
            8. Responde SOLO el comando.

            EJEMPLOS:
            Usuario: "Pon la hoja de hoy" -> hoja {fecha_hoy}
            Usuario: "Crea la segunda planilla" -> segunda planilla
            Usuario: "Abre una tercera planilla" -> tercera planilla
            Usuario: "Le di 40 lucas a Julian" -> trabajador 40000 julian
            Usuario: "Prestale 20 mil a Maria" -> trabajador 20000 maria
            Usuario: "Trabajador 20000 Mari cosina" -> trabajador 20000 mari cocina
            Usuario: "Vendí 150k en efectivo" -> efectivo 150000
            Usuario: "Le di un vale de 20k al administrador" -> administrador 20000
            Usuario: "Gasto autoservicio 20000" -> gasto 20000 autoservicio
            Usuario: "Gasto de aseo 15 mil" -> gasto 15000 aseo
            Usuario: "Compré azúcar por 60 mil" -> gasto 60000 azúcar
            Usuario: "Compré 2 millones de insumos" -> gasto 2000000 insumos
            Usuario: "Gasto 30000 d1" -> gasto 30000 d1
            Usuario: "D1 15 mil" -> gasto 15000 d1. (explicación: el usuario dijo "d1" que es un supermercado, por lo tanto es un gasto normal)
            Usuario: "Ara 15 mil" -> gasto 15000 ara. (explicación: el usuario dijo "ara" que es un supermercado, por lo tanto es un gasto normal)
            Usuario: "Mercaldas 30000" -> gasto 30000 mercaldas. (explicación: el usuario dijo "mercaldas" que es un supermercado, por lo tanto es un gasto normal)
            Usuario: "Compré 2 millones de insumos" -> gasto 2000000 insumos
            Usuario: "Retiro de 100k para el banco" -> retiro 100000 banco
            Usuario: "Retiro de 1 millon 300 para Levapan" -> retiro 1300000 levapan
            Usuario: "Compré jabón y escobas por 25 lucas" -> limpieza 25000
            Usuario: "Almuerzo para los trabajadores 30k" -> alimentacion 30000
            Usuario: "Comida del personal 20 lucas" -> alimentacion 20000
            Usuario: "Inversión de 500k en maquinaria" -> inversion 500000 maquinaria
            Usuario: "Págale la nómina de 200 mil a Peter" -> nomina 200000 peter
            Usuario: "Nomina de Maria por 150 mil" -> nomina 150000 maria
            Usuario: "Retiro de 200 mil para nómina de Peter" -> retiro 200000 nomina peter
            Usuario: "Retiro de 500 mil para la nómina de María" -> retiro 500000 nomina maria

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
