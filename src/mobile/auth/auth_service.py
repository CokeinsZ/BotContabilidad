"""Vinculación de la app desde WhatsApp y sesiones de la app.

Por qué así: `phone_number` puede ser un LID de WhatsApp (no un teléfono), así
que no se le puede pedir al administrador "escribe tu número" ni enviarle un
código a un número. En cambio, el bot ya sabe quién le escribe. Flujo:

1. La app pide una vinculación: recibe un id secreto y un código de 6 dígitos.
2. El administrador le envía "VINCULAR <código>" al bot por WhatsApp. El bot
   lo identifica como siempre (teléfono o LID) y confirma la vinculación.
3. La app consulta con su id secreto y recibe los tokens UNA sola vez.

Sin contraseñas que guardar ni recuperar; el registro sigue siendo por CLI.
"""
import re
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Callable
from urllib.parse import quote

from accounting.accounting_service import unregistered_message
from config.log import log_warning
from database.app_repository import CONFIRMED, CONSUMED, PENDING, AppRepository
from database.business_repository import BusinessRepository
from database.models import BusinessContext
from mobile.errors import NotFound, Unauthorized
from mobile.security.tokens import InvalidToken, TokenService

#: Cuánto vive un código de vinculación sin confirmar.
PAIRING_TTL_SECONDS = 5 * 60
#: Tiempo extra para que la app recoja los tokens después de confirmar.
PAIRING_PICKUP_SECONDS = 10 * 60

_PAIR_RE = re.compile(r"^\s*vincular\s*(?:la\s+)?(?:app\s*)?(\d{6})\s*\.?\s*$", re.IGNORECASE)
_CLOSE_RE = re.compile(r"^\s*cerrar\s+(?:la\s+)?app\s*\.?\s*$", re.IGNORECASE)
_PAIRING_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,100}$")

PENDIENTE = "pendiente"
CONFIRMADA = "confirmada"
CONSUMIDA = "consumida"
EXPIRADA = "expirada"


@dataclass(frozen=True)
class PairingStart:
    id: str
    code: str
    message: str               # lo que el administrador envía al bot
    whatsapp_url: str | None   # wa.me/<bot>?text=<mensaje> (None si no hay número configurado)
    expires_at: int
    expires_in: int


@dataclass(frozen=True)
class IssuedSession:
    access_token: str
    access_expires_in: int
    refresh_token: str
    context: BusinessContext


@dataclass(frozen=True)
class PairingPoll:
    state: str
    session: IssuedSession | None = None


class AppAuthService:
    def __init__(
        self,
        repository: AppRepository,
        businesses: BusinessRepository,
        tokens: TokenService,
        bot_whatsapp_number: str = "",
        clock: Callable[[], float] = time.time,
    ):
        self._repository = repository
        self._businesses = businesses
        self._tokens = tokens
        self._bot_number = bot_whatsapp_number
        self._clock = clock

    @property
    def enabled(self) -> bool:
        return self._tokens.enabled

    def _now(self) -> int:
        return int(self._clock())

    # ------------------------------------------------------------------
    # Vinculación
    # ------------------------------------------------------------------
    def start_pairing(self, device_name: str | None) -> PairingStart:
        now = self._now()
        self._repository.delete_expired_pairings(now)
        code = self._unused_code(now)
        pairing_id = uuid.uuid4().hex + secrets.token_hex(8)
        expires_at = now + PAIRING_TTL_SECONDS
        self._repository.create_pairing(pairing_id, code, _clean_device(device_name), expires_at, now)

        message = f"VINCULAR {code}"
        url = f"https://wa.me/{self._bot_number}?text={quote(message)}" if self._bot_number else None
        return PairingStart(
            id=pairing_id, code=code, message=message, whatsapp_url=url,
            expires_at=expires_at, expires_in=PAIRING_TTL_SECONDS,
        )

    def poll_pairing(self, pairing_id: str) -> PairingPoll:
        """Estado de una vinculación. Al confirmarse, entrega los tokens una sola vez."""
        if not _PAIRING_ID_RE.match(pairing_id or ""):
            raise NotFound("La vinculación no existe.", "VINCULACION_NO_EXISTE")
        record = self._repository.get_pairing(pairing_id)
        if record is None:
            raise NotFound("La vinculación no existe.", "VINCULACION_NO_EXISTE")

        now = self._now()
        if record.state == PENDING:
            return PairingPoll(EXPIRADA if record.expires_at <= now else PENDIENTE)
        if record.state == CONSUMED:
            return PairingPoll(CONSUMIDA)
        if record.state != CONFIRMED:
            return PairingPoll(EXPIRADA)
        if record.expires_at + PAIRING_PICKUP_SECONDS <= now:
            return PairingPoll(EXPIRADA)
        if not self._repository.consume_pairing(pairing_id):
            return PairingPoll(CONSUMIDA)   # otra consulta simultánea ganó

        context = self._businesses.find_context_by_admin_id(record.administrator_id)
        if context is None:
            raise Unauthorized(
                "Tu usuario ya no está activo. Habla con el proveedor del bot.", "USUARIO_INACTIVO"
            )
        return PairingPoll(CONFIRMADA, self._issue(context, record.device_name))

    @staticmethod
    def is_app_message(text: str | None) -> bool:
        """True si el texto es "VINCULAR <código>" o "cerrar app" (chequeo barato, sin base de datos)."""
        return bool(text) and (_PAIR_RE.match(text) is not None or _CLOSE_RE.match(text) is not None)

    def handle_whatsapp_text(self, phone_number: str, text: str) -> str | None:
        """Responde los mensajes de WhatsApp que son para la app.

        - "VINCULAR 482913": confirma la vinculación con ese código.
        - "cerrar app": revoca todas las sesiones de la app de quien escribe.

        Devuelve None si el mensaje no es para la app (sigue el flujo normal).
        """
        text = text or ""
        pair = _PAIR_RE.match(text)
        close = _CLOSE_RE.match(text)
        if pair is None and close is None:
            return None
        if not self.enabled:
            return "⚠️ La app móvil no está habilitada en este servidor."

        context = self._businesses.find_context_by_phone(phone_number)
        if context is None:
            return unregistered_message(phone_number)

        now = self._now()
        if close is not None:
            revoked = self._repository.revoke_sessions_of_admin(context.administrator.id, now)
            if revoked == 0:
                return "No tenías la app abierta en ningún dispositivo."
            return f"✅ Se cerró la app en {revoked} dispositivo(s)."

        record = self._repository.confirm_pairing(pair.group(1), context.administrator.id, now)
        if record is None:
            log_warning(
                "código de vinculación inválido o vencido",
                f"phone={phone_number} admin_id={context.administrator.id}",
            )
            return (
                "⚠️ El código de vinculación no es válido o ya venció. "
                "Genera uno nuevo en la app."
            )
        device = f" en {record.device_name}" if record.device_name else ""
        return (
            f"✅ App vinculada{device} para {context.business.name}.\n"
            "Si no fuiste tú, escribe 'cerrar app' para desconectarla."
        )

    # ------------------------------------------------------------------
    # Sesiones
    # ------------------------------------------------------------------
    def refresh(self, refresh_token: str) -> IssuedSession:
        """Cambia un refresh token por uno nuevo y un token de acceso nuevo."""
        now = self._now()
        old_hash = self._tokens.hash_refresh(refresh_token)
        session = self._repository.find_session_by_refresh_hash(old_hash)
        if session is None or not session.is_active(now):
            raise Unauthorized("Tu sesión terminó. Vincula la app de nuevo.", "SESION_TERMINADA")

        context = self._businesses.find_context_by_admin_id(session.administrator_id)
        if context is None:
            self._repository.revoke_session(session.id, now)
            raise Unauthorized(
                "Tu usuario ya no está activo. Habla con el proveedor del bot.", "USUARIO_INACTIVO"
            )

        new_token = self._tokens.new_refresh_token()
        rotated = self._repository.rotate_refresh(
            session.id, old_hash, self._tokens.hash_refresh(new_token),
            now + self._tokens.refresh_seconds, now,
        )
        if not rotated:
            raise Unauthorized("Tu sesión terminó. Vincula la app de nuevo.", "SESION_TERMINADA")
        return IssuedSession(
            access_token=self._tokens.issue_access(context.administrator.id, context.business.id, session.id),
            access_expires_in=self._tokens.access_seconds,
            refresh_token=new_token,
            context=context,
        )

    def logout(self, refresh_token: str) -> None:
        """Revoca la sesión de ese refresh token. Nunca falla (salir siempre funciona)."""
        session = self._repository.find_session_by_refresh_hash(self._tokens.hash_refresh(refresh_token))
        if session is not None:
            self._repository.revoke_session(session.id, self._now())

    def authenticate(self, access_token: str) -> BusinessContext:
        """Valida el token de acceso, que la sesión siga viva y que el usuario siga activo."""
        try:
            claims = self._tokens.verify_access(access_token)
        except InvalidToken:
            raise Unauthorized("El token de acceso no es válido o venció.", "TOKEN_INVALIDO")

        session = self._repository.get_session(claims.session_id)
        if (
            session is None
            or not session.is_active(self._now())
            or session.administrator_id != claims.administrator_id
        ):
            raise Unauthorized("Tu sesión terminó. Vincula la app de nuevo.", "SESION_TERMINADA")

        context = self._businesses.find_context_by_admin_id(claims.administrator_id)
        if context is None:
            raise Unauthorized(
                "Tu usuario ya no está activo. Habla con el proveedor del bot.", "USUARIO_INACTIVO"
            )
        return context

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _issue(self, context: BusinessContext, device_name: str | None) -> IssuedSession:
        now = self._now()
        refresh_token = self._tokens.new_refresh_token()
        session_id = self._repository.create_session(
            context.administrator.id,
            self._tokens.hash_refresh(refresh_token),
            device_name,
            now + self._tokens.refresh_seconds,
            now,
        )
        return IssuedSession(
            access_token=self._tokens.issue_access(context.administrator.id, context.business.id, session_id),
            access_expires_in=self._tokens.access_seconds,
            refresh_token=refresh_token,
            context=context,
        )

    def _unused_code(self, now: int) -> str:
        """Código de 6 dígitos que no choque con otra vinculación pendiente."""
        for _ in range(20):
            code = f"{secrets.randbelow(1_000_000):06d}"
            if not self._repository.code_in_use(code, now):
                return code
        raise RuntimeError("no se encontró un código de vinculación libre")


def _clean_device(device_name: str | None) -> str | None:
    if not device_name:
        return None
    cleaned = " ".join(device_name.split())[:60]
    return cleaned or None
