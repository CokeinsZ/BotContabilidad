"""
Punto de entrada de la aplicación (composition root).

Aquí se construyen e inyectan todas las dependencias. El arranque NUNCA se
bloquea por autenticación: si no hay credenciales de Google, el servidor
arranca igualmente y basta con abrir `/auth/login` desde cualquier
dispositivo para autenticarlo.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from accounting import (
    AccountingService,
    CommandDispatcher,
    SessionManager,
    build_default_commands,
)
from ai import DeepSeekService, WhisperService
from auth import GoogleAuthManager, create_auth_router
from config import Settings, get_settings
from database import BusinessRepository, Database
from drive import DriveClient
from sheets import SheetsClient
from whatsapp import WhatsAppService, create_whatsapp_router


class Container:
    """Contenedor de dependencias de la aplicación (DIP)."""

    def __init__(self, settings: Settings):
        self.settings = settings

        # Autenticación y persistencia
        self.auth_manager = GoogleAuthManager(
            client_secret_path=settings.google_client_secret_path,
            token_path=settings.google_token_path,
            redirect_uri=settings.google_oauth_redirect_uri,
        )
        self.database = Database(
            db_path=settings.database_path,
            schema_path=settings.database_schema_path,
        )
        self.business_repository = BusinessRepository(self.database)

        # Clientes de Google (agnósticos del business)
        self.sheets_client = SheetsClient(self.auth_manager)
        self.drive_client = DriveClient(
            self.auth_manager,
            planilla_template_id=settings.planilla_template_id,
            workers_template_id=settings.workers_template_id,
        )

        # Núcleo de contabilidad
        self.session_manager = SessionManager()
        self.dispatcher = CommandDispatcher(build_default_commands())
        self.accounting_service = AccountingService(
            dispatcher=self.dispatcher,
            business_repository=self.business_repository,
            session_manager=self.session_manager,
            sheets_client=self.sheets_client,
            drive_client=self.drive_client,
        )

        # Servicios de IA y mensajería
        self.whisper_service = WhisperService(settings.whisper_url)
        self.deepseek_service = DeepSeekService(
            api_url=settings.deepseek_api_url, api_key=settings.deepseek_api_key
        )
        self.whatsapp_service = WhatsAppService(
            evolution_base_url=settings.evolution_api_base_url,
            evolution_instance_name=settings.evolution_api_instance_name,
            evolution_token=settings.evolution_api_token,
            whisper_service=self.whisper_service,
            deepseek_service=self.deepseek_service,
            accounting_service=self.accounting_service,
        )


def create_server() -> FastAPI:
    container = Container(get_settings())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if container.auth_manager.is_authenticated():
            print("✅ Credenciales de Google cargadas correctamente.")
        else:
            print(
                "⚠️ No hay credenciales válidas de Google.\n"
                "   Abre /auth/login en cualquier dispositivo para autenticar "
                "el servidor."
            )
        yield

    app = FastAPI(
        title="Bot de Contabilidad",
        description="Sistema multi-empresa para la gestión de planillas de contabilidad.",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:8080",
            "http://localhost:8000",
            "https://contabilidad.notiasis.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(create_auth_router(container.auth_manager))
    app.include_router(create_whatsapp_router(container.whatsapp_service))

    return app


app = create_server()
