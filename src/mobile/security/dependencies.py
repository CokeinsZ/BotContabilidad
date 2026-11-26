"""Dependencias FastAPI de la API de la app."""
from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.models import BusinessContext
from mobile.auth import AppAuthService
from mobile.errors import ServiceUnavailable, Unauthorized

CurrentContext = Callable[..., BusinessContext]


def create_enabled_guard(auth: AppAuthService):
    """Sin APP_JWT_SECRET la API de la app responde 503 (como /auth sin contraseña)."""

    async def require_enabled() -> None:
        if not auth.enabled:
            raise ServiceUnavailable(
                "La API de la app está deshabilitada: configura APP_JWT_SECRET en el servidor.",
                "APP_DESHABILITADA",
            )

    return require_enabled


def create_current_context(auth: AppAuthService) -> CurrentContext:
    """Dependencia que exige `Authorization: Bearer <access_token>` y devuelve negocio + administrador."""
    bearer = HTTPBearer(auto_error=False)

    async def current_context(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> BusinessContext:
        if credentials is None or not credentials.credentials:
            raise Unauthorized("Falta el token de acceso.", "TOKEN_INVALIDO")
        return auth.authenticate(credentials.credentials)

    return current_context
