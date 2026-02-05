from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from google_auth.auth_controller import generate_credentials, router as auth_router
from whatsapp.whatsapp_controller import init_service, router as whatsapp_router

from google_drive.google_drive_service import DriveService
from google_sheets.google_sheets_service import PlanillaSheetService
from dispatcher.command_dispatcher import CommandDispatcher

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
            "http://localhost", "http://localhost:8080", "http://localhost:8000", 
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

@app.on_event("startup")
async def startup_event():
    # Aquí es donde se crea la instancia del CommandDispatcher
    sheets_service = PlanillaSheetService(credentials)
    drive_service = DriveService(credentials)
    
    dispatcher = CommandDispatcher(
        drive_service=drive_service,
        sheets_service=sheets_service
    )

    # Inicializar WhatsAppService con el dispatcher
    init_service(dispatcher)
    
