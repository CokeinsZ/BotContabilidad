"""
Endpoints HTTP del módulo de autenticación con Google.

Flujo completo (funciona desde cualquier dispositivo, sin SSH):

1. Abrir `https://<servidor>/auth/login` en el navegador de cualquier
   dispositivo → el servidor redirige a Google.
2. Iniciar sesión y conceder permisos en Google.
3. Google redirige a `/auth/callback` y el servidor guarda `token.json`
   automáticamente.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth.dto import AuthStatusResponse, MessageResponse
from auth.google_auth_manager import GoogleAuthManager

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


def create_auth_router(auth_manager: GoogleAuthManager) -> APIRouter:
    """Factory del router de autenticación (inyección de dependencias)."""
    router = APIRouter(prefix="/auth", tags=["Auth"])

    @router.get("/login")
    async def login():
        """Redirige al usuario a la pantalla de autorización de Google.

        Es el único enlace que hay que abrir para autenticar el servidor.
        """
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
        except Exception as error:
            raise HTTPException(
                status_code=500, detail=f"Error al completar la autenticación: {error}"
            )
        return _SUCCESS_HTML

    @router.get("/status", response_model=AuthStatusResponse)
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

    @router.post("/refresh-token", response_model=MessageResponse)
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
