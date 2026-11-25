"""
Endpoints HTTP del módulo de autenticación con Google.

Flujo completo (funciona desde cualquier dispositivo, sin SSH):

1. Abrir `https://<servidor>/auth/login` en el navegador de cualquier
   dispositivo → el navegador pide usuario y contraseña (HTTP Basic,
   AUTH_ADMIN_USER / AUTH_ADMIN_PASSWORD) → el servidor redirige a Google.
2. Iniciar sesión y conceder permisos en Google.
3. Google redirige a `/auth/callback` y el servidor guarda `token.json`.

Seguridad:
- `/login`, `/status` y `/refresh-token` exigen HTTP Basic. Sin
  AUTH_ADMIN_PASSWORD configurado, quedan deshabilitados (503).
- `/callback` no puede pedir Basic (lo llama Google por redirección), pero
  solo acepta un `state` emitido por un `/login` autenticado y vigente.
- Si GOOGLE_ALLOWED_EMAILS está configurado, solo esas cuentas de Google
  pueden quedar como credenciales del servidor.
"""
import asyncio
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from auth.dto import AuthStatusResponse, MessageResponse
from auth.google_auth_manager import AccountNotAllowedError, GoogleAuthManager
from config.log import log_warning

_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Autenticación exitosa</title></head>
<body style="font-family: sans-serif; text-align: center; padding-top: 4rem;">
    <h1>✅ Autenticación exitosa</h1>
    <p>El servidor ya recibió y guardó las credenciales de Google.</p>
    <p>Puedes cerrar esta pestaña.</p>
</body>
</html>
"""

#: Pausa ante credenciales inválidas (frena ataques de fuerza bruta).
FAILED_LOGIN_DELAY_SECONDS = 1.0


def create_admin_guard(admin_user: str, admin_password: str):
    """Dependencia FastAPI que exige HTTP Basic con las credenciales de admin."""
    basic = HTTPBasic(realm="Bot Contabilidad", auto_error=False)

    async def require_admin(
        request: Request, credentials: HTTPBasicCredentials | None = Depends(basic)
    ) -> None:
        if not admin_password:
            raise HTTPException(
                status_code=503,
                detail="Autenticación deshabilitada: configura AUTH_ADMIN_PASSWORD en el servidor.",
            )
        valid = credentials is not None and (
            secrets.compare_digest(credentials.username.encode(), admin_user.encode())
            & secrets.compare_digest(credentials.password.encode(), admin_password.encode())
        )
        if not valid:
            if credentials is not None:
                client = request.client.host if request.client else "?"
                log_warning("credenciales inválidas en /auth", f"path={request.url.path} client={client}")
                await asyncio.sleep(FAILED_LOGIN_DELAY_SECONDS)
            raise HTTPException(
                status_code=401,
                detail="Credenciales requeridas.",
                headers={"WWW-Authenticate": 'Basic realm="Bot Contabilidad"'},
            )

    return require_admin


def create_auth_router(
    auth_manager: GoogleAuthManager, admin_user: str, admin_password: str
) -> APIRouter:
    """Factory del router de autenticación (inyección de dependencias)."""
    router = APIRouter(prefix="/auth", tags=["Auth"])
    require_admin = create_admin_guard(admin_user, admin_password)

    @router.get("/login", dependencies=[Depends(require_admin)])
    async def login():
        """Redirige al usuario a la pantalla de autorización de Google."""
        try:
            authorization_url = auth_manager.create_authorization_url()
        except FileNotFoundError as error:
            raise HTTPException(status_code=500, detail=str(error))
        return RedirectResponse(authorization_url)

    @router.get("/callback", response_class=HTMLResponse)
    async def callback(request: Request):
        """Recibe el código de Google, lo intercambia y guarda el token."""
        error = request.query_params.get("error")
        if error:
            raise HTTPException(
                status_code=400, detail=f"Google rechazó la autorización: {error}"
            )
        try:
            auth_manager.complete_authorization(
                code=request.query_params.get("code"),
                state=request.query_params.get("state"),
                authorization_response=str(request.url),
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))
        except AccountNotAllowedError as error:
            raise HTTPException(status_code=403, detail=str(error))
        except Exception as error:
            raise HTTPException(
                status_code=500, detail=f"Error al completar la autenticación: {error}"
            )
        return _SUCCESS_HTML

    @router.get("/status", response_model=AuthStatusResponse, dependencies=[Depends(require_admin)])
    async def status():
        """Indica si el servidor posee credenciales válidas de Google."""
        if auth_manager.is_authenticated():
            return AuthStatusResponse(
                authenticated=True, message="Credenciales válidas disponibles."
            )
        return AuthStatusResponse(
            authenticated=False,
            message="No hay credenciales válidas. Abre /auth/login para autenticar.",
        )

    @router.post("/refresh-token", response_model=MessageResponse, dependencies=[Depends(require_admin)])
    async def refresh_token():
        """Refresca el token de acceso usando el refresh_token almacenado."""
        if auth_manager.refresh_credentials():
            return MessageResponse(
                status="success", message="Token refrescado exitosamente."
            )
        raise HTTPException(
            status_code=400,
            detail="No fue posible refrescar el token. Autentica de nuevo en /auth/login.",
        )

    return router
