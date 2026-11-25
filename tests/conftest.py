import pytest

from accounting import AccountingService, CommandDispatcher, SessionManager, build_default_commands
from database.models import Administrator, Business, BusinessContext
from sheets.sheets_client import SheetsClient

from fakes import FakeDrive, FakeSheetsService


# ----------------------------------------------------------------------
# Pruebas E2E: solo con `--e2e` (necesitan el entorno local levantado y
# usan DeepSeek y Google reales). Ver tests/e2e/README.md.
# ----------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", default=False,
                     help="Ejecuta las pruebas E2E contra el bot local y los servicios reales")


def pytest_collection_modifyitems(config, items):
    run_e2e = config.getoption("--e2e")
    skip = pytest.mark.skip(reason="prueba E2E: usa --e2e para ejecutarla")
    for item in items:
        if "/tests/e2e/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(pytest.mark.e2e)
            if not run_e2e:
                item.add_marker(skip)
        elif run_e2e:
            item.add_marker(pytest.mark.skip(reason="con --e2e solo se ejecutan las pruebas E2E"))


BUSINESS = Business(3, "Pruebas", "folder-planillas", "folder-trabajadores", "active")
ADMINS = {
    "999": Administrator(7, 3, "Admin de prueba", "999", "active"),
    "998": Administrator(8, 3, "Otro admin", "998", "active"),
}


class FakeSheetsClient(SheetsClient):
    def __init__(self, service):
        super().__init__(auth_manager=None)
        self._fake_service = service

    @property
    def service(self):
        return self._fake_service


class FakeRepository:
    def find_context_by_phone(self, phone):
        admin = ADMINS.get(phone)
        return BusinessContext(BUSINESS, admin) if admin else None


class Bot:
    """Atajo para enviar mensajes (listas de comandos) como un admin."""

    def __init__(self):
        self.service = FakeSheetsService()
        self.sheets = FakeSheetsClient(self.service)
        self.drive = FakeDrive(self.service)
        self.sessions = SessionManager()
        self.accounting = AccountingService(
            CommandDispatcher(build_default_commands()),
            FakeRepository(),
            self.sessions,
            self.sheets,
            self.drive,
        )

    def send(self, *commands: str, phone: str = "999") -> list[str]:
        return self.accounting.handle_commands(phone, list(commands))

    def session(self, phone: str = "999"):
        return self.sessions.get_or_create(BUSINESS.id, phone)

    def active_file(self, phone: str = "999"):
        return self.service.files[self.session(phone).active_sheet_id]


@pytest.fixture
def bot():
    return Bot()
