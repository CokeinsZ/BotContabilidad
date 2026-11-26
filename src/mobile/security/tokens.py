"""Tokens de la app móvil.

- Acceso: JWT HS256 de vida corta (por defecto 60 min). Lleva el
  administrador, su negocio y la sesión (`sid`); en cada petición se revisa
  en SQLite que la sesión siga activa, así revocarla corta el acceso al
  instante y no cuando venza el JWT.
- Refresco: 32 bytes aleatorios. En la base solo queda su SHA-256 y cambia en
  cada uso (rotación).
"""
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Callable

import jwt

ACCESS_TOKEN_TYPE = "app_access"


class InvalidToken(Exception):
    """El token de acceso no es válido, está mal firmado o venció."""


@dataclass(frozen=True)
class AccessClaims:
    administrator_id: int
    business_id: int
    session_id: int


class TokenService:
    ALGORITHM = "HS256"

    def __init__(
        self,
        secret: str,
        access_minutes: int = 60,
        refresh_days: int = 90,
        clock: Callable[[], float] = time.time,
    ):
        self._secret = secret
        self.access_seconds = access_minutes * 60
        self.refresh_seconds = refresh_days * 86_400
        self._clock = clock

    @property
    def enabled(self) -> bool:
        """Sin secreto no se firman tokens: la API de la app queda apagada."""
        return bool(self._secret)

    def issue_access(self, administrator_id: int, business_id: int, session_id: int) -> str:
        now = int(self._clock())
        payload = {
            "sub": str(administrator_id),
            "bid": business_id,
            "sid": session_id,
            "typ": ACCESS_TOKEN_TYPE,
            "iat": now,
            "exp": now + self.access_seconds,
        }
        return jwt.encode(payload, self._secret, algorithm=self.ALGORITHM)

    def verify_access(self, token: str) -> AccessClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self.ALGORITHM],
                options={"require": ["exp", "iat", "sub", "sid", "bid"]},
                leeway=10,
            )
        except jwt.PyJWTError as error:
            raise InvalidToken(str(error)) from error
        if payload.get("typ") != ACCESS_TOKEN_TYPE:
            raise InvalidToken("tipo de token inesperado")
        try:
            return AccessClaims(
                administrator_id=int(payload["sub"]),
                business_id=int(payload["bid"]),
                session_id=int(payload["sid"]),
            )
        except (TypeError, ValueError) as error:
            raise InvalidToken("claims inválidos") from error

    @staticmethod
    def new_refresh_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_refresh(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
