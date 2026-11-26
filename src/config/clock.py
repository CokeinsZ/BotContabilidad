"""Reloj de la aplicación en la zona horaria del negocio.

El contenedor corre en UTC: `datetime.now()` a secas devolvía el día
siguiente entre las 7 p. m. y la medianoche de Colombia. Todo cálculo de
"hoy" debe pasar por este módulo.
"""
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from config.settings import get_settings

DATE_FORMAT = "%d-%m-%Y"


@lru_cache(maxsize=1)
def business_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def now() -> datetime:
    """Fecha y hora actuales en la zona horaria del negocio."""
    return datetime.now(business_timezone())


def today_str() -> str:
    """Fecha de hoy (zona del negocio) en formato dd-mm-aaaa."""
    return now().strftime(DATE_FORMAT)
