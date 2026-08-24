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
    master_folder_id: str
    planilla_template_id: str

    # --- Google OAuth ---
    google_client_secret_path: Path
    google_token_path: Path
    google_oauth_redirect_uri: str

    # --- Base de datos ---
    database_path: Path
    database_schema_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            evolution_api_base_url=_env("EVOLUTION_API_BASE_URL", "http://evolution-api:8080"),
            evolution_api_instance_name=_env("EVOLUTION_API_INSTANCE_NAME", ""),
            evolution_api_token=_env("EVOLUTION_API_TOKEN", ""),
            whisper_url=_env("WHISPER_URL", ""),
            deepseek_api_url=_env("DEEPSEEK_API_URL", "https://api.deepseek.com"),
            deepseek_api_key=_env("DEEPSEEK_API_KEY", ""),
            master_folder_id=_env("MASTER_FOLDER_ID", ""),
            planilla_template_id=_env("PLANILLA_TEMPLATE_ID", ""),
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
            database_path=Path(
                _env("DATABASE_PATH", str(PROJECT_ROOT / "data" / "bot_contabilidad.db"))
            ),
            database_schema_path=Path(
                _env("DATABASE_SCHEMA_PATH", str(PROJECT_ROOT / "db.sql"))
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia única de configuración (singleton)."""
    return Settings.from_env()
