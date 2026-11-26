"""
Configuración centralizada de la aplicación.

Expone un objeto `Settings` inmutable construido una única vez desde las
variables de entorno. Toda dependencia de configuración debe recibirse por
inyección (SRP/DIP): los módulos no deben leer `os.getenv` directamente.
"""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def _env(key: str, default: str) -> str:
    """Lee una variable de entorno tratando el string vacío como no definido."""
    value = os.getenv(key)
    return value if value else default


def _env_list(key: str) -> tuple[str, ...]:
    """Lee una lista separada por comas (vacía si no está definida)."""
    raw = os.getenv(key, "")
    return tuple(item.strip().lower() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Configuración global de la aplicación (inmutable)."""

    # --- Evolution API (WhatsApp) ---
    evolution_api_base_url: str
    evolution_api_instance_name: str
    evolution_api_token: str

    # --- Servicios de IA ---
    whisper_url: str
    deepseek_api_url: str
    deepseek_api_key: str

    # --- Google Drive (valores universales a todos los businesses) ---
    planilla_template_id: str
    workers_template_id: str

    # --- Google OAuth ---
    google_client_secret_path: Path
    google_token_path: Path
    google_oauth_redirect_uri: str
    # Cuentas de Google con las que se permite autenticar el servidor.
    # Vacío = cualquier cuenta (no recomendado en producción).
    google_allowed_emails: tuple[str, ...]

    # --- Protección de los endpoints /auth (HTTP Basic) ---
    # Sin contraseña configurada, /auth/login queda deshabilitado.
    auth_admin_user: str
    auth_admin_password: str

    # --- Base de datos ---
    database_path: Path
    database_schema_path: Path

    # --- Zona horaria del negocio ("hoy", fechas de nómina, etc.) ---
    timezone: str

    # --- API de la app móvil (/app) ---
    # Sin secreto configurado, la API de la app queda deshabilitada (503).
    app_jwt_secret: str
    app_access_token_minutes: int
    app_refresh_token_days: int
    # Número de WhatsApp del bot (solo dígitos, con indicativo): la app abre
    # wa.me/<número> para que el administrador envíe el código de vinculación.
    bot_whatsapp_number: str
    # Códigos de vinculación que puede pedir una misma IP cada 10 minutos.
    app_pairings_per_ip: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            evolution_api_base_url=_env("EVOLUTION_API_BASE_URL", "http://evolution-api:8080"),
            evolution_api_instance_name=_env("EVOLUTION_API_INSTANCE_NAME", ""),
            evolution_api_token=_env("EVOLUTION_API_TOKEN", ""),
            whisper_url=_env("WHISPER_URL", ""),
            deepseek_api_url=_env("DEEPSEEK_API_URL", "https://api.deepseek.com"),
            deepseek_api_key=_env("DEEPSEEK_API_KEY", ""),
            planilla_template_id=_env("PLANILLA_TEMPLATE_ID", ""),
            workers_template_id=_env("WORKERS_TEMPLATE_ID", ""),
            google_client_secret_path=Path(
                _env("GOOGLE_CLIENT_SECRET_PATH", str(PROJECT_ROOT / "client_secret.json"))
            ),
            google_token_path=Path(
                _env("GOOGLE_TOKEN_PATH", str(PROJECT_ROOT / "token.json"))
            ),
            google_oauth_redirect_uri=_env(
                "GOOGLE_OAUTH_REDIRECT_URI",
                "https://contabilidad.notiasis.com/auth/callback",
            ),
            google_allowed_emails=_env_list("GOOGLE_ALLOWED_EMAILS"),
            auth_admin_user=_env("AUTH_ADMIN_USER", "admin"),
            auth_admin_password=_env("AUTH_ADMIN_PASSWORD", ""),
            database_path=Path(
                _env("DATABASE_PATH", str(PROJECT_ROOT / "data" / "bot_contabilidad.db"))
            ),
            database_schema_path=Path(
                _env("DATABASE_SCHEMA_PATH", str(PROJECT_ROOT / "db.sql"))
            ),
            timezone=_env("TIMEZONE", "America/Bogota"),
            app_jwt_secret=_env("APP_JWT_SECRET", ""),
            app_access_token_minutes=int(_env("APP_ACCESS_TOKEN_MINUTES", "60")),
            app_refresh_token_days=int(_env("APP_REFRESH_TOKEN_DAYS", "90")),
            bot_whatsapp_number="".join(filter(str.isdigit, _env("BOT_WHATSAPP_NUMBER", ""))),
            app_pairings_per_ip=int(_env("APP_PAIRINGS_PER_IP", "10")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia única de configuración (singleton)."""
    return Settings.from_env()
