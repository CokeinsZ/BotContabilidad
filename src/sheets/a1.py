"""Utilidades mínimas de notación A1 ("principal!B13", "C11:D11", ...)."""
import re

_CELL_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def split_sheet(range_a1: str) -> tuple[str, str]:
    """'principal!A1:B2' -> ('principal!', 'A1:B2'); 'A1' -> ('', 'A1')."""
    if "!" in range_a1:
        sheet, cells = range_a1.rsplit("!", 1)
        return f"{sheet}!", cells
    return "", range_a1


def column_number(letters: str) -> int:
    """'A' -> 1, 'Z' -> 26, 'AA' -> 27."""
    number = 0
    for char in letters.upper():
        number = number * 26 + (ord(char) - ord("A") + 1)
    return number


def column_letters(number: int) -> str:
    """1 -> 'A', 27 -> 'AA'."""
    letters = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def parse_cell(cell: str) -> tuple[int, int]:
    """'C13' -> (3, 13) como (columna, fila)."""
    match = _CELL_RE.match(cell)
    if not match:
        raise ValueError(f"Celda A1 inválida: {cell!r}")
    return column_number(match.group(1)), int(match.group(2))


def range_start(range_a1: str) -> tuple[str, int, int]:
    """Prefijo de hoja, columna y fila de la esquina superior izquierda."""
    prefix, cells = split_sheet(range_a1)
    column, row = parse_cell(cells.split(":")[0])
    return prefix, column, row


def cell_at(prefix: str, column: int, row: int) -> str:
    return f"{prefix}{column_letters(column)}{row}"
