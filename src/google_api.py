"""Ejecución de peticiones a las APIs de Google: reintentos y una conexión por hilo.

Reintentos: Google Sheets limita las peticiones por minuto POR USUARIO (≈60
escrituras/minuto) y el bot usa una sola cuenta para todos los negocios: un
mensaje con muchos comandos, o varios administradores a la vez, pueden recibir
`429 RATE_LIMIT_EXCEEDED`. Antes eso hacía fallar el comando de inmediato;
ahora se espera con backoff exponencial hasta que la cuota se libera.

Una conexión por hilo: cada cliente (Drive, Sheets) construye su servicio una
sola vez, y todas sus peticiones compartían el mismo `httplib2.Http`, que NO es
seguro entre hilos. Los comandos de WhatsApp y las lecturas de la app corren en
hilos distintos (`asyncio.to_thread`); cuando dos usaban la misma conexión TLS
a la vez, OpenSSL mezclaba los datos (`SSLError: RECORD_LAYER_FAILURE`, falsos
404/502) y el proceso terminaba con SIGSEGV/SIGABRT. Ahora cada hilo usa su
propio `Http` con las mismas credenciales (lo que recomienda la documentación
de google-api-python-client, "Thread Safety"). La conexión de cada hilo se
reutiliza entre peticiones.
"""
import random
import threading
import time

import google_auth_httplib2
from googleapiclient.errors import HttpError
from googleapiclient.http import build_http

from config.log import log_warning

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_WAIT_SECONDS = 120.0   # la cuota es por minuto: cubre una ventana completa
MAX_DELAY_SECONDS = 32.0

_thread = threading.local()


def thread_http(request):
    """`Http` autorizado del hilo actual para las credenciales de `request`.

    Devuelve None si la petición no trae credenciales de google-auth (p. ej.
    los dobles de prueba): entonces se ejecuta con su propio `http`.
    """
    credentials = getattr(getattr(request, "http", None), "credentials", None)
    if credentials is None:
        return None
    http = getattr(_thread, "http", None)
    if http is None or http.credentials is not credentials:   # primera vez o re-login
        http = google_auth_httplib2.AuthorizedHttp(credentials, http=build_http())
        _thread.http = http
    return http


def execute(request, *, max_wait: float = MAX_WAIT_SECONDS, sleep=time.sleep):
    """Ejecuta `request` con la conexión del hilo, reintentando ante cuota excedida y 5xx."""
    http = thread_http(request)
    delay = 1.0
    waited = 0.0
    while True:
        try:
            return request.execute(http=http) if http is not None else request.execute()
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
