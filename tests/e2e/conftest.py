"""Fixtures E2E: una corrida = una carpeta de Drive y negocios temporales."""
import os
from datetime import datetime

import httpx
import pytest

from e2e_support import (
    BOT_URL, DB_PATH, KEEP_ARTIFACTS, MOCK_URL, E2EDatabase, Google, Run,
)


def _require_services() -> None:
    try:
        httpx.get(f"{MOCK_URL}/messages", timeout=5).raise_for_status()
        httpx.get(f"{BOT_URL}/auth/status", timeout=5)
    except httpx.HTTPError as error:
        pytest.fail(
            "El entorno local no está levantado "
            f"({error}). Ejecuta: docker compose -f docker-compose.local.yml up -d --build",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def run():
    _require_services()
    parent = os.getenv("E2E_DRIVE_FOLDER_ID")
    if not parent:
        pytest.fail("Define E2E_DRIVE_FOLDER_ID en el .env", pytrace=False)

    google = Google()
    db = E2EDatabase(DB_PATH)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    root = google.create_folder(f"E2E {stamp}", parent)
    planillas = google.create_folder("planillas", root)
    trabajadores = google.create_folder("trabajadores", root)
    no_workers_planillas = google.create_folder("planillas-sin-trabajadores", root)
    business_id = db.add_business(f"E2E {stamp}", planillas, trabajadores)
    no_workers_business_id = db.add_business(f"E2E sin trabajadores {stamp}", no_workers_planillas, None)

    run = Run(google, db, stamp, root, planillas, trabajadores, business_id,
              no_workers_planillas, no_workers_business_id)
    print(f"\n📁 Corrida E2E: https://drive.google.com/drive/folders/{root}")
    try:
        yield run
    finally:
        for created in (business_id, no_workers_business_id, *run.extra_businesses):
            db.delete_business(created)
        if KEEP_ARTIFACTS:
            print(f"\n📁 Archivos conservados (E2E_KEEP=1): https://drive.google.com/drive/folders/{root}")
        else:
            google.trash(root)


@pytest.fixture
def google(run):
    return run.google


@pytest.fixture
def admin(run):
    """Un administrador nuevo por prueba (sesión limpia: sin planilla ni deshacer)."""
    return run.new_admin("Admin E2E")


@pytest.fixture
def admin2(run):
    return run.new_admin("Segundo admin E2E")
