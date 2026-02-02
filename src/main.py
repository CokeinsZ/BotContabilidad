from google_auth.auth_manager import GoogleAuthManager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from google_auth.auth_controller import generate_credentials, router as auth_router
from whatsapp.whatsapp_controller import router as whatsapp_router

def create_server() -> FastAPI:
    app = FastAPI(
        title="Pan de Oro Contabilidad", 
        description="Sistema para la gestión de planillas de Pan de Oro",
        version="1.0.0"
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost", "http://localhost:8080", 
            "http://158.69.193.190", "http://158.69.193.190:8080",
            "https://oauth.cokeinsz.com"
        ],
        allow_credentials=True,
        allow_methods=[
            "GET", "POST", "OPTIONS"
        ],
        allow_headers=["*"],
    )

    # Configurar autenticación HTTP Bearer
    app.security = HTTPBearer()

    app.include_router(auth_router)
    app.include_router(whatsapp_router)

    return app


credentials = generate_credentials()
app = create_server()
