"""Utilidades para el nombrado de planillas diarias.

Convención de nombres:
- Primera planilla del día:  `dd-mm-yyyy`        (ordinal 1)
- Planillas adicionales:     `dd-mm-yyyy-N`      (ordinal N >= 2)
"""
from datetime import datetime

#: Palabras ordinales en español para los comandos "segunda planilla", etc.
ORDINAL_WORDS = {
    2: "segunda",
    3: "tercera",
    4: "cuarta",
    5: "quinta",
    6: "sexta",
    7: "séptima",
    8: "octava",
    9: "novena",
    10: "décima",
    11: "undécima",
    12: "duodécima",
}

#: Límite de planillas adicionales soportadas por día.
MAX_DAILY_SHEETS = 31


def is_valid_date_name(name: str) -> bool:
    """True si `name` tiene formato de fecha dd-mm-yyyy válido."""
    try:
        datetime.strptime(name, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def base_date_of(sheet_name: str) -> str | None:
    """Extrae la fecha base de un nombre de planilla.

    "25-08-2026" -> "25-08-2026"
    "25-08-2026-2" -> "25-08-2026"
    """
    candidate = sheet_name[:10]
    return candidate if is_valid_date_name(candidate) else None


def sheet_name_for(date_str: str, ordinal: int) -> str:
    """Nombre de archivo para la planilla N-ésima de un día."""
    return date_str if ordinal == 1 else f"{date_str}-{ordinal}"
