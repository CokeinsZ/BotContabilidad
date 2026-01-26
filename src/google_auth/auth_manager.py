"""
Módulo de autenticación con Google OAuth 2.0.

Proporciona funcionalidades para autenticarse con Google usando
credenciales OAuth 2.0 desde client_secret.json.
"""

import os
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes necesarios para acceder a Google Sheets y Drive
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Rutas por defecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CLIENT_SECRET_PATH = PROJECT_ROOT / "client_secret.json"
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "token.json"


class GoogleAuthManager:
    """Gestiona la autenticación con Google OAuth 2.0."""

    def __init__(
        self,
        client_secret_path = None,
        token_path = None,
        scopes = None,
    ):
        """
        Inicializa el gestor de autenticación.

        Args:
            client_secret_path: Ruta al archivo client_secret.json.
            token_path: Ruta donde se guardará/leerá el token.
            scopes: Lista de scopes de Google API requeridos.
        """
        self.client_secret_path = client_secret_path or DEFAULT_CLIENT_SECRET_PATH
        self.token_path = token_path or DEFAULT_TOKEN_PATH
        self.scopes = scopes or SCOPES
        self._credentials = None

    def get_credentials(self) -> Credentials:
        """
        Obtiene las credenciales de Google, autenticando si es necesario.

        Si existe un token guardado y es válido, lo usa.
        Si el token ha expirado pero tiene refresh_token, lo renueva.
        Si no hay token válido, inicia el flujo de autenticación OAuth.

        Returns:
            Credentials: Credenciales válidas de Google.

        Raises:
            FileNotFoundError: Si no se encuentra el archivo client_secret.json.
        """
        if self._credentials and self._credentials.valid:
            return self._credentials

        # Intentar cargar credenciales existentes
        if self.token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self.token_path), self.scopes
            )

        # Verificar si las credenciales son válidas
        if self._credentials and self._credentials.valid:
            return self._credentials

        # Intentar refrescar si el token expiró
        if (
            self._credentials
            and self._credentials.expired
            and self._credentials.refresh_token
        ):
            self._credentials.refresh(Request())
            self._save_credentials()
            return self._credentials

        # Iniciar flujo de autenticación OAuth
        if not self.client_secret_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de credenciales: {self.client_secret_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.client_secret_path), self.scopes
        )

        # Ejecutar el servidor local para la autenticación (puerto fijo para OAuth)
        self._credentials = flow.run_local_server(port=8080)
        self._save_credentials()

        return self._credentials

    def _save_credentials(self) -> None:
        """Guarda las credenciales en el archivo de token."""
        if self._credentials:
            with open(self.token_path, "w") as token_file:
                token_file.write(self._credentials.to_json())

    def revoke_credentials(self) -> bool:
        """
        Revoca las credenciales actuales.

        Returns:
            bool: True si se revocaron exitosamente, False en caso contrario.
        """
        if self._credentials:
            try:
                import requests

                requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": self._credentials.token},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                )
                self._credentials = None

                # Eliminar el archivo de token
                if self.token_path.exists():
                    self.token_path.unlink()

                return True
            except Exception:
                return False
        return False

    def is_authenticated(self) -> bool:
        """
        Verifica si hay una sesión autenticada válida.

        Returns:
            bool: True si está autenticado, False en caso contrario.
        """
        try:
            creds = self.get_credentials()
            return creds is not None and creds.valid
        except Exception:
            return False
