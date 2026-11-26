"""Montos: parseo tolerante al formato colombiano y formato de salida.

En Colombia el punto es separador de miles: "5.000" son cinco mil pesos,
no cinco. `float("5.000")` daba 5.0 (un error de x1000).
"""
import math
import re

_DOT_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")     # 1.234.567 / 2.500,50
_COMMA_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")   # 1,234,567 / 2,500.50
_COMMA_DECIMAL = re.compile(r"^-?\d+,\d{1,2}$")                   # 2500,5 / 2500,50


def parse_amount(raw: str) -> float:
    """Convierte un monto escrito por una persona en número.

    Acepta "5000", "5.000", "$5.000", "1.200.000", "5,000", "2.500,50" y
    "2500.50". Lanza ValueError si no es un monto válido.
    """
    text = str(raw).strip().replace("$", "").replace(" ", "")
    if _DOT_THOUSANDS.match(text):
        text = text.replace(".", "").replace(",", ".")
    elif _COMMA_THOUSANDS.match(text):
        text = text.replace(",", "")
    elif _COMMA_DECIMAL.match(text):
        text = text.replace(",", ".")
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"Monto no finito: {raw!r}")
    return value


def cell_number(value: float) -> int | float:
    """Número para escribir en la planilla (5000 en vez de 5000.0)."""
    return int(value) if float(value).is_integer() else value


def format_amount(value) -> str:
    """5000 -> "$5.000"; 2500.5 -> "$2.500,50". Si no es número, lo deja igual."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if float(value).is_integer():
        text = f"{int(value):,}".replace(",", ".")
    else:
        text = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{sign}${text}"
