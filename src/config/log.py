"""Logging centralizado: que CUALQUIER error salga en los logs con contexto.

Problema que resuelve: varios puntos del código hacían
`print(f"Error ...: {error}")` (solo el mensaje) o directamente
`return False` / `return None` sin loguear nada. Resultado: el usuario
recibía "⚠️ No se pudo registrar..." y en los logs no había forma de
saber por qué (¿contador vacío? ¿HttpError de Google? ¿planilla sin
layout? ¿credenciales vencidas?).

Uso:
    from config.log import log_error, log_warning

    try:
        ...
    except Exception as error:
        log_error("escribiendo rangos", error, f"sheet_id={sheet_id} ranges={...}")
        return False

    # Fallos SIN excepción (un `return False` por validación) también se loguean:
    if counter is None:
        log_warning("append_to_region sin contador", f"sheet_id={...} ...")
        return False
"""
import traceback


def _http_error_detail(error: BaseException) -> str:
    """Extrae status/reason/content de un HttpError de Google (si lo es)."""
    resp = getattr(error, "resp", None)
    content = getattr(error, "content", None)
    if resp is None and content is None:
        return ""
    status = getattr(resp, "status", "?") if resp is not None else "?"
    reason = getattr(resp, "reason", "") if resp is not None else ""
    if isinstance(content, (bytes, bytearray)):
        try:
            content = bytes(content).decode("utf-8", errors="replace")
        except Exception:
            content = repr(content)
    # Recortar contenidos gigantes (la API a veces devuelve HTML enorme).
    if isinstance(content, str) and len(content) > 2000:
        content = content[:2000] + "... [truncado]"
    return f" | http_status={status} reason={reason} content={content}"


def log_error(context: str, error: BaseException, extra: str = "") -> None:
    """Loguea una excepción con tipo, detalle HTTP (si aplica) y traceback.

    Args:
        context: qué se estaba haciendo ("leyendo rangos", "ejecutando comando gasto", ...).
        error: la excepción capturada.
        extra: contexto clave=valor (sheet_id, comando, teléfono, rango, ...).
    """
    detail = _http_error_detail(error)
    tb = traceback.format_exc()
    # `traceback.format_exc()` devuelve "NoneType: None" si no hay excepción
    # activa (llamada fuera de un except); en ese caso no lo mostramos.
    tb_block = "" if "NoneType: None" in tb else f"\n{tb.rstrip()}"
    suffix = f" | {extra}" if extra else ""
    print(
        f"❌ ERROR {context}{suffix} -> "
        f"{type(error).__name__}: {error}{detail}{tb_block}",
        flush=True,
    )


def log_warning(context: str, extra: str = "") -> None:
    """Loguea un fallo SIN excepción (ej: un `return False` por validación).

    Estos eran los más peligrosos: no dejaban ningún rastro. Siempre
    incluir en `extra` los datos que permiten diagnosticar (sheet_id,
    celda contador, valor leído, comando, etc.).
    """
    suffix = f" | {extra}" if extra else ""
    print(f"⚠️ FALLO {context}{suffix}", flush=True)
