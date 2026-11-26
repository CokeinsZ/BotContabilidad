"""Perfil para la app: administrador, negocio y ediciones de nombre."""
from dataclasses import dataclass
from typing import Callable

from config.clock import today_str
from database.business_repository import BusinessRepository
from database.models import Administrator, BusinessContext
from mobile.errors import Unauthorized, Unprocessable
from mobile.google_gate import GoogleGate

NAME_MIN = 2
NAME_MAX = 80


@dataclass(frozen=True)
class Profile:
    context: BusinessContext
    administrators: list[Administrator]   # activos del negocio, incluido quien consulta
    today: str
    google_connected: bool
    bot_whatsapp_number: str


class ProfileService:
    def __init__(
        self,
        businesses: BusinessRepository,
        google: GoogleGate,
        bot_whatsapp_number: str = "",
        today: Callable[[], str] = today_str,
    ):
        self._businesses = businesses
        self._google = google
        self._bot_number = bot_whatsapp_number
        self._today = today

    def profile(self, ctx: BusinessContext) -> Profile:
        fresh = self._businesses.find_context_by_admin_id(ctx.administrator.id)
        if fresh is None:
            raise Unauthorized(
                "Tu usuario ya no está activo. Habla con el proveedor del bot.", "USUARIO_INACTIVO"
            )
        administrators = [
            admin for admin in self._businesses.list_administrators(fresh.business.id)
            if admin.state == "active"
        ]
        return Profile(
            context=fresh,
            administrators=administrators,
            today=self._today(),
            google_connected=self._google.connected,
            bot_whatsapp_number=self._bot_number,
        )

    def rename_business(self, ctx: BusinessContext, name: str) -> Profile:
        """El nombre nuevo se usa en las planillas nuevas (A2); las existentes no cambian."""
        self._businesses.update_business_name(ctx.business.id, clean_name(name))
        return self.profile(ctx)

    def rename_administrator(self, ctx: BusinessContext, name: str) -> Profile:
        """El nombre nuevo se usa en las planillas nuevas (B6); las existentes no cambian."""
        self._businesses.update_administrator_name(ctx.administrator.id, clean_name(name))
        return self.profile(ctx)


def clean_name(raw: str) -> str:
    name = " ".join((raw or "").split())
    if not NAME_MIN <= len(name) <= NAME_MAX:
        raise Unprocessable(
            f"El nombre debe tener entre {NAME_MIN} y {NAME_MAX} caracteres.", "NOMBRE_INVALIDO"
        )
    return name
