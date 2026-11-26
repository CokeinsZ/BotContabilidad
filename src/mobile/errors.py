"""Errores de la API de la app.

Cada error se responde como `{"detail": "<mensaje legible>", "codigo": "<CODIGO>"}`
(ver `api.install_mobile_api`). La app muestra `detail` y decide por `codigo`.
"""


class AppError(Exception):
    status = 400
    code = "ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or type(self).code


class Unauthorized(AppError):
    status = 401
    code = "NO_AUTORIZADO"


class NotFound(AppError):
    status = 404
    code = "NO_ENCONTRADO"


class Conflict(AppError):
    status = 409
    code = "CONFLICTO"


class Unprocessable(AppError):
    status = 422
    code = "DATOS_INVALIDOS"


class TooManyRequests(AppError):
    status = 429
    code = "DEMASIADAS_SOLICITUDES"


class BadGateway(AppError):
    """Google o DeepSeek fallaron: se puede reintentar."""

    status = 502
    code = "SERVICIO_EXTERNO"


class ServiceUnavailable(AppError):
    status = 503
    code = "NO_DISPONIBLE"
