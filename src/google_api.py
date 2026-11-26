"""Ejecución de peticiones a las APIs de Google con reintentos.

Google Sheets limita las peticiones por minuto POR USUARIO (≈60 escrituras/
minuto) y el bot usa una sola cuenta para todos los negocios: un mensaje con
muchos comandos, o varios administradores a la vez, pueden recibir
`429 RATE_LIMIT_EXCEEDED`. Antes eso hacía fallar el comando de inmediato;
ahora se espera con backoff exponencial hasta que la cuota se libera.
"""
import random
import time

from googleapiclient.errors import HttpError

from config.log import log_warning

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_WAIT_SECONDS = 120.0   # la cuota es por minuto: cubre una ventana completa
MAX_DELAY_SECONDS = 32.0


def execute(request, *, max_wait: float = MAX_WAIT_SECONDS, sleep=time.sleep):
    """Ejecuta `request` reintentando ante cuota excedida y errores 5xx."""
    delay = 1.0
    waited = 0.0
    while True:
        try:
            return request.execute()
        except HttpError as error:
            status = getattr(error.resp, "status", None)
            if status not in RETRYABLE_STATUS or waited >= max_wait:
                raise
            pause = min(delay, MAX_DELAY_SECONDS) * random.uniform(0.75, 1.0)
            log_warning(
                f"Google respondió {status}, reintentando",
                f"espera={pause:.1f}s acumulado={waited:.1f}s uri={getattr(request, 'uri', '?')[:120]}",
            )
            sleep(pause)
            waited += pause
            delay *= 2
