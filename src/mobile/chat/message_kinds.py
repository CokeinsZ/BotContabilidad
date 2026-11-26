"""Tipo de cada respuesta del bot, para que la app la pinte con su ícono.

Las respuestas del bot son textos pensados para WhatsApp, con un emoji al
inicio. La app no muestra el emoji: dibuja su propio ícono según el tipo.
"""
EXITO = "exito"
AVISO = "aviso"
ERROR = "error"
INFO = "info"
SELECCION = "seleccion"

#: Emoji inicial -> tipo. None = "⚠️": aviso o error según el texto.
_EMOJI_KINDS = (
    ("⚠️", None),
    ("⚠", None),
    ("✅", EXITO),
    ("📄", EXITO),
    ("🔄", EXITO),
    ("👤", INFO),
    ("📋", INFO),
    ("⏳", INFO),
    ("🤔", INFO),
)
_ERROR_MARKERS = ("error interno", "no se pudo", "no se pudieron")
_WARNING_STARTS = ("no existe",)
_INFO_STARTS = ("link a la planilla", "no hay ")


def classify(text: str) -> tuple[str, str]:
    """(tipo, texto sin el emoji inicial)."""
    stripped = (text or "").strip()
    for emoji, kind in _EMOJI_KINDS:
        if stripped.startswith(emoji):
            body = stripped[len(emoji):].lstrip("️").strip()
            if kind is None:
                kind = ERROR if any(marker in body.lower() for marker in _ERROR_MARKERS) else AVISO
            return kind, body
    lowered = stripped.lower()
    if lowered.startswith(_WARNING_STARTS):
        return AVISO, stripped
    if lowered.startswith(_INFO_STARTS):
        return INFO, stripped
    return EXITO, stripped
