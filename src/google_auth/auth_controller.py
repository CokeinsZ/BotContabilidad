"""
Controlador para endpoints de autenticación con Google.

Proporciona endpoints para gestionar la autenticación y renovación de tokens.
"""

from fastapi import APIRouter, HTTPException

from google_auth.auth_manager import GoogleAuthManager

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_manager = GoogleAuthManager()


@router.post("/refresh-token")
async def refresh_token():
    """
    Endpoint para refrescar el token de autenticación con Google.
    
    No requiere interacción del usuario. El token se renueva automáticamente
    si existe un refresh_token válido.
    
    Returns:
        dict: Estado de la operación y mensaje descriptivo.
        
    Raises:
        HTTPException: 400 si no hay credenciales o 500 si hay error al refrescar.
    """
    try:
        if auth_manager.refresh_credentials():
            return {
                "status": "success",
                "message": "Token refrescado exitosamente"
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al refrescar el token: {str(e)}"
        )
    
def generate_credentials():
    credentials = auth_manager.get_credentials()
    print("Autenticación exitosa. Credenciales obtenidas.")
    return credentials
