"""
Gestor de autenticación con Google OAuth 2.0 orientado a servidor.

A diferencia del flujo clásico de escritorio (`run_local_server`, que exige un
navegador en la misma máquina), este gestor implementa el flujo de
*aplicación web* con `redirect_uri`:

1. El servidor genera una URL de autorización (`create_authorization_url`).
2. El usuario abre esa URL en CUALQUIER dispositivo e inicia sesión con Google.
3. Google redirige a `<redirect_uri>?code=...&state=...` (este mismo servidor).
4. El servidor intercambia el código por tokens, verifica que la cuenta esté
   permitida y guarda `token.json` (`complete_authorization`).

Requisito: el `redirect_uri` debe estar registrado como
"URI de redireccionamiento autorizado" en la consola de Google Cloud.
"""
import os
import threading
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config.log import log_error, log_warning

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

#: Tiempo que vive un `state` emitido por /auth/login (anti-CSRF).
STATE_TTL_SECONDS = 10 * 60


class AccountNotAllowedError(PermissionError):
    """La cuenta de Google con la que se inició sesión no está permitida."""


class GoogleAuthManager:
    """Gestiona el ciclo de vida de las credenciales OAuth de Google."""

    def __init__(
        self,
        client_secret_path: Path,
        token_path: Path,
        redirect_uri: str,
        allowed_emails: tuple[str, ...] = (),
        scopes: list[str] | None = None,
    ):
        self._client_secret_path = client_secret_path
        self._token_path = token_path
        self._redirect_uri = redirect_uri
        self._allowed_emails = tuple(email.lower() for email in allowed_emails)
        self._scopes = scopes or SCOPES

        self._credentials: Credentials | None = None
        # state pendiente -> (code_verifier PKCE o None, instante de emisión)
        self._pending_states: dict[str, tuple[str | None, float]] = {}
        self._lock = threading.Lock()

        if self._redirect_uri.startswith("http://"):
            # Permite probar el flujo en entornos locales sin HTTPS.
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # ------------------------------------------------------------------
    # Flujo OAuth remoto (login desde cualquier dispositivo)
    # ------------------------------------------------------------------
    def create_authorization_url(self) -> str:
        """Genera la URL de autorización de Google.

        Raises:
            FileNotFoundError: si no existe el archivo client_secret.
        """
        if not self._client_secret_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de credenciales: {self._client_secret_path}"
            )

        flow = self._build_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",  # imprescindible para obtener refresh_token
            prompt="consent",       # fuerza refresh_token en re-autorizaciones
            include_granted_scopes="true",
        )
        with self._lock:
            self._purge_expired_states()
            # google-auth-oauthlib usa PKCE: el code_verifier vive en el flow
            # que generó la URL y debe reutilizarse al intercambiar el código.
            self._pending_states[state] = (getattr(flow, "code_verifier", None), time.monotonic())
        return authorization_url

    def complete_authorization(
        self, *, code: str | None, state: str | None, authorization_response: str
    ) -> Credentials:
        """Intercambia el código de Google por tokens y los persiste.

        Raises:
            ValueError: si faltan parámetros o el state no es válido/expiró.
            AccountNotAllowedError: si la cuenta no está en la lista permitida.
        """
        if not code:
            raise ValueError("Google no devolvió el parámetro 'code'.")
        with self._lock:
            self._purge_expired_states()
            if state is None or state not in self._pending_states:
                raise ValueError(
                    "El parámetro 'state' no es válido o la sesión expiró. "
                    "Inicia el proceso de autenticación de nuevo."
                )
            code_verifier, _issued_at = self._pending_states.pop(state)

        flow = self._build_flow()
        if code_verifier:
            # Restaurar el verifier PKCE del flow que generó la URL,
            # de lo contrario Google responde "invalid_grant: Missing code verifier".
            flow.code_verifier = code_verifier
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        if self._allowed_emails:
            email = (self.fetch_account_email(credentials) or "").lower()
            if email not in self._allowed_emails:
                log_warning("intento de autenticación con cuenta no permitida", f"email={email!r}")
                raise AccountNotAllowedError(
                    f"La cuenta '{email}' no está autorizada para este servidor."
                )
        else:
            log_warning(
                "GOOGLE_ALLOWED_EMAILS vacío: se acepta cualquier cuenta de Google",
                "configúralo en el .env para restringirlo",
            )

        self._credentials = credentials
        self._save_credentials()
        return self._credentials

    def fetch_account_email(self, credentials: Credentials) -> str | None:
        """Correo de la cuenta de Google dueña de las credenciales."""
        try:
            drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
            about = drive.about().get(fields="user(emailAddress)").execute()
            return about.get("user", {}).get("emailAddress")
        except Exception as error:
            log_error("obteniendo el correo de la cuenta de Google", error)
            return None

    # ------------------------------------------------------------------
    # Obtención y refresco de credenciales (sin interacción del usuario)
    # ------------------------------------------------------------------
    def get_credentials(self) -> Credentials | None:
        """Devuelve credenciales válidas, o None si aún no hay autenticación.

        Nunca bloquea ni abre navegadores: es seguro llamarlo en el arranque
        del servidor. Refresca el token automáticamente cuando es posible.
        """
        if self._credentials and self._credentials.valid:
            return self._credentials

        if self._credentials is None and self._token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_path), self._scopes
            )

        if self._credentials and self._credentials.valid:
            return self._credentials

        if (
            self._credentials
            and self._credentials.expired
            and self._credentials.refresh_token
        ):
            if self.refresh_credentials():
                return self._credentials
            return None

        return None

    def refresh_credentials(self) -> bool:
        """Refresca el token usando el refresh_token. Devuelve éxito/fallo."""
        if self._credentials is None and self._token_path.exists():
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_path), self._scopes
            )

        if not self._credentials or not self._credentials.refresh_token:
            return False

        try:
            self._credentials.refresh(Request())
            self._save_credentials()
            return True
        except Exception as error:
            log_error("refrescando token de Google", error)
            return False

    def is_authenticated(self) -> bool:
        return self.get_credentials() is not None

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _purge_expired_states(self) -> None:
        now = time.monotonic()
        expired = [
            state for state, (_verifier, issued_at) in self._pending_states.items()
            if now - issued_at > STATE_TTL_SECONDS
        ]
        for state in expired:
            del self._pending_states[state]

    def _build_flow(self) -> Flow:
        return Flow.from_client_secrets_file(
            str(self._client_secret_path),
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
        )

    def _save_credentials(self) -> None:
        if self._credentials:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._token_path, "w", encoding="utf-8") as token_file:
                token_file.write(self._credentials.to_json())
