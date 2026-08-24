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
            evolution_api_base_url=os.getenv("EVOLUTION_API_BASE_URL", "http://evolution-api:8080"),
            evolution_api_instance_name=os.getenv("EVOLUTION_API_INSTANCE_NAME", ""),
            evolution_api_token=os.getenv("EVOLUTION_API_TOKEN", ""),
            whisper_url=os.getenv("WHISPER_URL", ""),
            deepseek_api_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            master_folder_id=os.getenv("MASTER_FOLDER_ID", ""),
            planilla_template_id=os.getenv("PLANILLA_TEMPLATE_ID", ""),
            google_client_secret_path=Path(
                os.getenv("GOOGLE_CLIENT_SECRET_PATH", str(PROJECT_ROOT / "client_secret.json"))
            ),
            google_token_path=Path(
                os.getenv("GOOGLE_TOKEN_PATH", str(PROJECT_ROOT / "token.json"))
            ),
            google_oauth_redirect_uri=os.getenv(
                "GOOGLE_OAUTH_REDIRECT_URI",
                "https://contabilidad.notiasis.com/auth/callback",
            ),
            database_path=Path(
                os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "bot_contabilidad.db"))
            ),
            database_schema_path=Path(
                os.getenv("DATABASE_SCHEMA_PATH", str(PROJECT_ROOT / "db.sql"))
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la instancia única de configuración (singleton)."""
    return Settings.from_env()
