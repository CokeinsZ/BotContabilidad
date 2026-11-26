"""Conversión de valores de celda para la API."""


def number_or_none(value) -> int | float | None:
    """El valor si es un número de verdad (no bool, no texto); si no, None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def int_or_none(value) -> int | None:
    number = number_or_none(value)
    if number is None or not float(number).is_integer():
        return None
    return int(number)


def sheet_url(file_id: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{file_id}/edit"


def folder_url(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"
