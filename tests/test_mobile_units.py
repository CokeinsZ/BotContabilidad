"""Piezas de la API de la app sin servidor: parser de comandos, tipos de respuesta, tokens, catálogo."""
import time

import pytest

from accounting import CommandDispatcher, build_default_commands
from mobile.cache import TtlCache
from mobile.catalog import CATALOG, find_entry
from mobile.chat.command_builder import strict_command
from mobile.chat.message_kinds import AVISO, ERROR, EXITO, INFO, classify
from mobile.security import InvalidToken, SlidingWindowLimiter, TokenService

SECRET = "s" * 48


# ----------------------------------------------------------------------
# Parser estricto (lo que se registra sin DeepSeek)
# ----------------------------------------------------------------------
@pytest.mark.parametrize("command, text, expected", [
    ("gasto", "5.000 pan", "gasto 5000 pan"),
    ("gasto", "pan 5.000", "gasto 5000 pan"),
    ("gasto", "$1.200.000 harina de trigo", "gasto 1200000 harina de trigo"),
    ("gasto", "5000 de pan", "gasto 5000 pan"),
    ("gasto", "30000 d1", "gasto 30000 d1"),
    ("retiro", "100.000 nomina juan", "retiro 100000 nomina juan"),
    ("trabajador", "juan 20000", "trabajador 20000 juan"),
    ("trabajador", "20.000 maria jose", "trabajador 20000 maria jose"),
    ("efectivo", "350.000", "efectivo 350000"),
    ("saldo", "2.500,50", "saldo 2500.5"),
    ("deshacer", "", "deshacer"),
    ("terminar_dia", "lo que sea", "terminar_dia"),
])
def test_strict_command_reads_well_written_text(command, text, expected):
    assert strict_command(find_entry(command), text) == expected


@pytest.mark.parametrize("command, text", [
    ("gasto", "5 mil de pan"),        # "5 mil" no son 5 pesos
    ("gasto", "2 millones insumos"),
    ("gasto", "5k pan"),
    ("gasto", "pan"),                 # sin monto
    ("gasto", "5000"),                # sin descripción
    ("gasto", "5000 pan 2"),          # dos números: ¿cuál es el monto?
    ("gasto", "pan 5000 2"),
    ("efectivo", "350 mil"),
    ("efectivo", "cero"),
    ("saldo", "-500"),
    ("trabajador", "20 lucas juan"),
])
def test_strict_command_leaves_the_rest_to_deepseek(command, text):
    assert strict_command(find_entry(command), text) is None


# ----------------------------------------------------------------------
# Tipo de cada respuesta del bot
# ----------------------------------------------------------------------
@pytest.mark.parametrize("text, kind, clean", [
    ("Gasto registrado: $5.000 - pan", EXITO, "Gasto registrado: $5.000 - pan"),
    ("✅ Se deshizo: gasto 5000 pan.", EXITO, "Se deshizo: gasto 5000 pan."),
    ("⚠️ La sección 'aseo' de la planilla está llena (8 filas).", AVISO,
     "La sección 'aseo' de la planilla está llena (8 filas)."),
    ("⚠️ No se pudo registrar el movimiento en la planilla.", ERROR,
     "No se pudo registrar el movimiento en la planilla."),
    ("⚠️ Ocurrió un error interno al procesar el comando.", ERROR,
     "Ocurrió un error interno al procesar el comando."),
    ("📄 Préstamo guardado en el archivo de 'juan'.", EXITO, "Préstamo guardado en el archivo de 'juan'."),
    ("👤 Se creó el archivo del trabajador 'juan'.", INFO, "Se creó el archivo del trabajador 'juan'."),
    ("No existe una planilla para el día anterior: '23-11-2026'", AVISO,
     "No existe una planilla para el día anterior: '23-11-2026'"),
    ("🤔 No encontré ningún comando en tu mensaje.", INFO, "No encontré ningún comando en tu mensaje."),
])
def test_classify_bot_replies(text, kind, clean):
    assert classify(text) == (kind, clean)


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------
def test_access_token_roundtrip():
    tokens = TokenService(SECRET)
    claims = tokens.verify_access(tokens.issue_access(7, 3, 11))
    assert (claims.administrator_id, claims.business_id, claims.session_id) == (7, 3, 11)


def test_expired_tampered_or_foreign_tokens_are_rejected():
    old = TokenService(SECRET, access_minutes=60, clock=lambda: time.time() - 2 * 3600)
    with pytest.raises(InvalidToken):
        TokenService(SECRET).verify_access(old.issue_access(7, 3, 11))

    token = TokenService(SECRET).issue_access(7, 3, 11)
    with pytest.raises(InvalidToken):
        TokenService("otro-secreto-" + "x" * 40).verify_access(token)
    with pytest.raises(InvalidToken):
        TokenService(SECRET).verify_access(token[:-2] + "xx")


def test_refresh_tokens_are_random_and_hashed():
    first, second = TokenService.new_refresh_token(), TokenService.new_refresh_token()
    assert first != second and len(first) >= 40
    assert TokenService.hash_refresh(first) != first
    assert len(TokenService.hash_refresh(first)) == 64


# ----------------------------------------------------------------------
# Catálogo, límites y caché
# ----------------------------------------------------------------------
def test_every_catalog_command_exists_in_the_dispatcher():
    dispatcher = CommandDispatcher(build_default_commands())
    for entry in CATALOG:
        command = dispatcher.resolve(entry.id)
        assert command is not None and command.name == entry.id, entry.id


def test_catalog_has_no_sheet_commands():
    assert find_entry("hoja") is None and find_entry("segunda planilla") is None


def test_sliding_window_limiter():
    now = [0.0]
    limiter = SlidingWindowLimiter(max_events=2, window_seconds=10, clock=lambda: now[0])
    assert limiter.allow("ip") and limiter.allow("ip")
    assert not limiter.allow("ip")
    assert limiter.allow("otra-ip")
    now[0] = 11
    assert limiter.allow("ip")


def test_ttl_cache_expires_and_does_not_store_none():
    now = [0.0]
    cache = TtlCache(ttl_seconds=5, clock=lambda: now[0])
    calls = []

    def load():
        calls.append(1)
        return "valor"

    assert cache.get_or_load("k", load) == "valor"
    assert cache.get_or_load("k", load) == "valor"
    assert len(calls) == 1
    now[0] = 6
    assert cache.get_or_load("k", load) == "valor"
    assert len(calls) == 2
    assert cache.get_or_load("nada", lambda: None) is None
    assert cache.get("nada") is None
