"""Pruebas unitarias: montos, nombres, layout, reloj y parseo de DeepSeek."""
from datetime import datetime, timezone
from itertools import combinations

import pytest

from accounting.money import format_amount, parse_amount
from accounting.names import clean_worker_name, name_matches
from ai.deepseek_service import build_prompt, parse_commands
from config import clock
from sheets.a1 import column_number
from sheets.layout import PlanillaLayout


@pytest.mark.parametrize("raw, expected", [
    ("5000", 5000), ("5.000", 5000), ("$5.000", 5000), ("1.200.000", 1200000),
    ("5,000", 5000), ("2.500,50", 2500.5), ("2500.50", 2500.5), ("2500,5", 2500.5),
    ("$ 20.000", 20000), ("0", 0),
])
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("raw", ["pan", "", "nan", "inf", "5.000.00"])
def test_parse_amount_invalid(raw):
    with pytest.raises(ValueError):
        parse_amount(raw)


def test_format_amount():
    assert format_amount(5000) == "$5.000"
    assert format_amount(5000.0) == "$5.000"
    assert format_amount(1234567) == "$1.234.567"
    assert format_amount(2500.5) == "$2.500,50"
    assert format_amount(-5000) == "-$5.000"
    assert format_amount("#VALUE!") == "#VALUE!"


def test_worker_names_ignore_case_and_accents():
    assert clean_worker_name("  María   JOSÉ ") == "maria jose"
    assert clean_worker_name("Muñoz") == "muñoz"
    assert name_matches("maria jose", "María José")      # archivo creado a mano
    assert name_matches("MARÍA", "maria jose")
    assert name_matches("munoz", "Muñoz Pérez")
    assert name_matches("muñoz", "MUNOZ")
    assert name_matches("chloe", "Chloë")
    assert not name_matches("pedro", "maria")


def _cells(region):
    first, _, last = region.target_columns.split("!")[-1].partition(":")
    cols = range(column_number(first), column_number(last or first) + 1)
    return {(c, r) for c in cols for r in range(region.min_row, region.max_row + 1)}


def test_daily_regions_do_not_overlap_and_stay_above_totals():
    layout = PlanillaLayout()
    regions = [
        layout.expense_region, layout.worker_loan_region, layout.admin_region,
        layout.withdraw_region, layout.investment_region, layout.cleaning_region,
        layout.feeding_region,
    ]
    for a, b in combinations(regions, 2):
        assert not (_cells(a) & _cells(b)), f"{a.label} se solapa con {b.label}"
    totals = {(2, 38), (2, 39), (2, 40), (2, 42), (2, 58)}
    for region in regions:
        assert not (_cells(region) & totals), f"{region.label} pisa los totales"


def test_worker_region_matches_template():
    region = PlanillaLayout().worker_file_region
    assert region.block_range(13, 28) == "principal!A13:C28"
    assert region.capacity == 16
    assert region.blank_row == ["", 0, ""]
    assert region.row_range(15) == "principal!A15:C15"


def test_today_uses_business_timezone(monkeypatch):
    # 24-nov 23:30 en Bogotá = 25-nov 04:30 UTC: "hoy" debe seguir siendo el 24.
    instant = datetime(2026, 11, 25, 4, 30, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    monkeypatch.setattr(clock, "datetime", FrozenDatetime)
    assert clock.today_str() == "24-11-2026"
    assert "FECHA DE HOY: 24-11-2026" in build_prompt()


@pytest.mark.parametrize("content, expected", [
    ('{"comandos": ["gasto 5000 pan", "gasto 3000 leche"]}', ["gasto 5000 pan", "gasto 3000 leche"]),
    ('{"comandos": []}', []),
    ('```json\n{"comandos": ["Deshacer"]}\n```', ["deshacer"]),
    ('["resumen"]', ["resumen"]),
    ("gasto 5000 pan\ngasto 3000 leche", ["gasto 5000 pan", "gasto 3000 leche"]),
    ('{"otra": 1}', []),
    ("", []),
])
def test_parse_commands(content, expected):
    assert parse_commands(content) == expected


# ----------------------------------------------------------------------
# Reintentos ante la cuota de Google (429) y errores 5xx
# ----------------------------------------------------------------------
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from googleapiclient.errors import HttpError

from google_api import execute, thread_http


class FlakyRequest:
    uri = "https://sheets.googleapis.com/v4/..."

    def __init__(self, failures: list[int]):
        self.failures = list(failures)
        self.calls = 0

    def execute(self):
        self.calls += 1
        if self.failures:
            status = self.failures.pop(0)
            raise HttpError(SimpleNamespace(status=status, reason="x"), b"quota")
        return {"ok": True}


def test_execute_retries_quota_and_server_errors():
    sleeps = []
    request = FlakyRequest([429, 429, 503])
    assert execute(request, sleep=sleeps.append) == {"ok": True}
    assert request.calls == 4
    assert len(sleeps) == 3 and sleeps[0] < sleeps[1] < sleeps[2]   # backoff creciente


def test_execute_does_not_retry_client_errors():
    request = FlakyRequest([400])
    with pytest.raises(HttpError):
        execute(request, sleep=lambda s: None)
    assert request.calls == 1


def test_execute_gives_up_after_max_wait():
    request = FlakyRequest([429] * 50)
    with pytest.raises(HttpError):
        execute(request, max_wait=10, sleep=lambda s: None)
    assert request.calls < 50


class RecordingRequest:
    """Petición de google-api-python-client: trae el `http` autorizado del servicio."""

    def __init__(self, credentials):
        self.http = SimpleNamespace(credentials=credentials)
        self.used = []

    def execute(self, http=None):
        self.used.append(http)
        return {"ok": True}


def test_each_thread_gets_its_own_google_connection():
    # httplib2 no es seguro entre hilos: dos hilos con la misma conexión TLS
    # tumbaban el proceso (SIGSEGV) cuando la app pedía varias pantallas a la vez.
    credentials = SimpleNamespace()
    first, second = (thread_http(RecordingRequest(credentials)) for _ in range(2))
    with ThreadPoolExecutor(max_workers=1) as pool:
        other_thread = pool.submit(thread_http, RecordingRequest(credentials)).result()

    assert first is second                      # se reutiliza dentro del hilo
    assert other_thread is not first            # cada hilo, su conexión
    assert first.credentials is credentials
    assert thread_http(RecordingRequest(SimpleNamespace())) is not first   # re-login: conexión nueva


def test_execute_runs_the_request_on_the_thread_connection():
    request = RecordingRequest(SimpleNamespace())
    assert execute(request) == {"ok": True}
    assert request.used == [thread_http(request)]
