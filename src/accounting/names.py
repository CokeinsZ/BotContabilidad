"""Normalización de nombres de trabajadores (mayúsculas, tildes, espacios)."""
import unicodedata

_COMBINING_TILDE = "̃"


def _strip_marks(text: str, keep_enie: bool) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    kept: list[str] = []
    for char in decomposed:
        if unicodedata.combining(char):
            # La ñ (n + tilde) es una letra distinta en español: se conserva
            # en el nombre visible, pero no en la clave de búsqueda.
            if keep_enie and char == _COMBINING_TILDE and kept and kept[-1] in "nN":
                kept.append(char)
            continue
        kept.append(char)
    return unicodedata.normalize("NFC", "".join(kept))


def clean_worker_name(raw: str) -> str:
    """Nombre con el que se registra y se crea el archivo del trabajador.

    "  María   JOSÉ " -> "maria jose"; "Muñoz" -> "muñoz".
    """
    return " ".join(_strip_marks(raw, keep_enie=True).lower().split())


def name_key(text: str) -> str:
    """Clave de comparación: sin mayúsculas, tildes, diéresis ni ñ.

    Se aplica a AMBOS lados (lo que escribe el usuario y el nombre del
    archivo en Drive), así "María" (archivo creado a mano) coincide con
    "maria" y "MUÑOZ" con "munoz".
    """
    return " ".join(_strip_marks(text, keep_enie=False).casefold().split())


def name_matches(search: str, file_name: str) -> bool:
    """True si el nombre del archivo contiene el nombre buscado."""
    return name_key(search) in name_key(file_name)
