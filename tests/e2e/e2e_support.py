"""Soporte de las pruebas E2E.

- `BotUser`: un administrador que escribe al bot por el webhook real de
  WhatsApp (Evolution simulada) y recibe sus respuestas.
- `Google`: lectura/escritura directa en Drive y Sheets para verificar lo
  que hizo el bot (con el mismo token.json que usa el bot).
- `E2EDatabase`: registra negocios y administradores temporales en la base
  local que usa el contenedor.
"""
import os
import random
import re
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.settings import PROJECT_ROOT, get_settings  # también carga el .env
from drive.drive_client import DriveClient

BOT_URL = os.getenv("E2E_BOT_URL", "http://localhost:8000")
MOCK_URL = os.getenv("E2E_MOCK_URL", "http://localhost:8081")
DB_PATH = Path(os.getenv("E2E_DB_PATH", PROJECT_ROOT / "bot_contabilidad.db"))
TOKEN_PATH = Path(os.getenv("E2E_TOKEN_PATH", PROJECT_ROOT / "token.json"))
KEEP_ARTIFACTS = os.getenv("E2E_KEEP") == "1"

SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
RETRIES = 6


def today_str() -> str:
    """Hoy en la zona horaria del negocio (la misma que usa el bot)."""
    return datetime.now(ZoneInfo(get_settings().timezone)).strftime("%d-%m-%Y")


# ----------------------------------------------------------------------
# Bot (webhook real + Evolution simulada)
# ----------------------------------------------------------------------
class BotUser:
    """Un administrador conversando con el bot."""

    def __init__(self, phone: str, name: str):
        self.phone = phone
        self.name = name
        self.jid = f"{phone}@s.whatsapp.net"

    def post(self, text: str, message_id: str | None = None) -> tuple[str, dict]:
        """Envía el webhook SIN esperar el procesamiento. Devuelve (id, respuesta)."""
        message_id = message_id or uuid.uuid4().hex.upper()
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": self.jid, "fromMe": False, "id": message_id},
                "messageType": "conversation",
                "message": {"conversation": text},
            },
        }
        response = httpx.post(f"{BOT_URL}/whatsapp/messages-upsert", json=payload, timeout=30)
        response.raise_for_status()
        print(f"\n👤 [{self.name}] {text}")
        return message_id, response.json()

    @staticmethod
    def wait_done(message_id: str, timeout: float = 600) -> None:
        """Espera a que el bot termine de procesar el mensaje (en segundo plano)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = httpx.get(f"{BOT_URL}/whatsapp/messages/{message_id}/status").json()["status"]
            if status == "done":
                return
            time.sleep(0.3)
        raise TimeoutError(f"el mensaje {message_id} no terminó en {timeout}s")

    def replies_since(self, since: int) -> list[str]:
        replies = [
            m["text"] for m in httpx.get(f"{MOCK_URL}/messages", params={"since": since}).json()
            if m["to"] == self.jid
        ]
        for reply in replies:
            print("🤖 " + reply.replace("\n", "\n   "))
        return replies

    def send(self, text: str) -> list[str]:
        """Envía un mensaje, espera a que se procese y devuelve las respuestas."""
        since = last_mock_id()
        message_id, body = self.post(text)
        assert body.get("status") == "received", body
        self.wait_done(message_id)
        return self.replies_since(since)


class AppClient:
    """La app móvil de un administrador: se vincula por WhatsApp y usa la API /app."""

    def __init__(self, user: BotUser, session: dict):
        self.user = user
        self.access_token = session["access_token"]
        self.refresh_token = session["refresh_token"]
        self.profile = session["perfil"]

    @classmethod
    def pair(cls, user: BotUser, device: str = "E2E") -> "AppClient":
        """Vinculación completa: pedir código, enviarlo por WhatsApp y recoger la sesión."""
        start = httpx.post(f"{BOT_URL}/app/auth/vinculaciones", json={"dispositivo": device}, timeout=30)
        assert start.status_code == 201, start.text
        pairing = start.json()
        replies = user.send(pairing["mensaje"])
        assert replies and replies[0].startswith("✅ App vinculada"), replies
        poll = httpx.get(f"{BOT_URL}/app/auth/vinculaciones/{pairing['vinculacion_id']}", timeout=30).json()
        assert poll["estado"] == "confirmada", poll
        return cls(user, poll["sesion"])

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        return httpx.request(method, f"{BOT_URL}/app{path}", headers=self.headers, timeout=300, **kwargs)

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def ok(self, method: str, path: str, **kwargs):
        """JSON de una petición que debe responder 2xx."""
        response = self.request(method, path, **kwargs)
        assert response.is_success, f"{method} {path} -> {response.status_code} {response.text}"
        return response.json() if response.content else None

    def create(self, fecha: str, hoja: int = 1) -> dict:
        result = self.ok("POST", "/planillas", json={"fecha": fecha, "hoja": hoja})
        print(f"\n📱 [{self.user.name}] crear {fecha} hoja {hoja} -> creada={result['creada']}")
        for message in result["mensajes"]:
            print(f"🤖 ({message['tipo']}) {message['texto']}")
        return result

    def send(self, sheet_id: str, texto: str, comando: str | None = None,
             client_id: str | None = None) -> dict:
        """Envía un mensaje al chat de la planilla y devuelve el resultado."""
        client_id = client_id or f"e2e-{uuid.uuid4().hex}"
        label = f"{comando}: " if comando else ""
        print(f"\n📱 [{self.user.name}] {label}{texto}")
        result = self.ok("POST", f"/planillas/{sheet_id}/mensajes",
                         json={"client_id": client_id, "comando": comando, "texto": texto})
        for reply in result["respuestas"]:
            print(f"🤖 ({reply['tipo']}) " + reply["texto"].replace("\n", "\n   "))
        return result

    @staticmethod
    def texts(result: dict) -> list[str]:
        return [reply["texto"] for reply in result["respuestas"]]


def last_mock_id() -> int:
    return max((m["id"] for m in httpx.get(f"{MOCK_URL}/messages").json()), default=0)


def menu_options(menu: str) -> dict[str, int]:
    """Opciones de un menú numerado: {'jose salon': 1, ..., '__crear__': 3}."""
    options = {}
    for number, label in re.findall(r"^(\d+)\. (.+)$", menu, flags=re.M):
        key = "__crear__" if label.startswith("➕") else label.strip()
        options[key] = int(number)
    return options


# ----------------------------------------------------------------------
# Google (verificación directa)
# ----------------------------------------------------------------------
class Google:
    def __init__(self):
        credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH))
        self.sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        self.drive = build("drive", "v3", credentials=credentials, cache_discovery=False)

    @staticmethod
    def _x(request):
        return request.execute(num_retries=RETRIES)

    # --- Drive -----------------------------------------------------------
    def create_folder(self, name: str, parent: str) -> str:
        body = {"name": name, "mimeType": FOLDER_MIME, "parents": [parent]}
        return self._x(self.drive.files().create(body=body, fields="id"))["id"]

    def trash(self, file_id: str) -> None:
        self._x(self.drive.files().update(fileId=file_id, body={"trashed": True}))

    def children(self, folder_id: str, mime: str | None = SHEET_MIME) -> list[tuple[str, str]]:
        query = f"'{folder_id}' in parents and trashed=false"
        if mime:
            query += f" and mimeType='{mime}'"
        files = self._x(self.drive.files().list(q=query, fields="files(id,name)", pageSize=200))
        return [(f["id"], f["name"]) for f in files.get("files", [])]

    def child(self, folder_id: str, name: str, mime: str = SHEET_MIME) -> str | None:
        matches = [fid for fid, n in self.children(folder_id, mime) if n == name]
        assert len(matches) <= 1, f"hay {len(matches)} archivos llamados {name!r}"
        return matches[0] if matches else None

    def planilla(self, planillas_folder: str, name: str) -> str | None:
        """Id de la planilla `name` dentro de la carpeta del mes correspondiente."""
        month = self.child(planillas_folder, DriveClient.month_folder_name_for(name), FOLDER_MIME)
        return self.child(month, name) if month else None

    def planillas_of(self, planillas_folder: str, month_name: str) -> list[str]:
        month = self.child(planillas_folder, month_name, FOLDER_MIME)
        return sorted(name for _, name in self.children(month)) if month else []

    def copy(self, file_id: str, name: str, parent: str) -> str:
        body = {"name": name, "parents": [parent]}
        return self._x(self.drive.files().copy(fileId=file_id, body=body, fields="id"))["id"]

    def create_spreadsheet(self, name: str, parent: str) -> str:
        body = {"name": name, "mimeType": SHEET_MIME, "parents": [parent]}
        return self._x(self.drive.files().create(body=body, fields="id"))["id"]

    # --- Sheets ----------------------------------------------------------
    def values(self, file_id: str, *ranges: str, render: str = "UNFORMATTED_VALUE") -> list[list[list]]:
        response = self._x(self.sheets.spreadsheets().values().batchGet(
            spreadsheetId=file_id, ranges=list(ranges), valueRenderOption=render))
        return [vr.get("values", []) for vr in response.get("valueRanges", [])]

    def value(self, file_id: str, a1: str, render: str = "UNFORMATTED_VALUE"):
        rows = self.values(file_id, a1, render=render)[0]
        return rows[0][0] if rows and rows[0] else ""

    def cells(self, file_id: str, *a1s: str, render: str = "UNFORMATTED_VALUE") -> dict:
        """{celda: valor} para varias celdas sueltas en una sola llamada."""
        result = self.values(file_id, *a1s, render=render)
        return {a1: (rows[0][0] if rows and rows[0] else "") for a1, rows in zip(a1s, result)}

    def column(self, file_id: str, range_a1: str, render: str = "UNFORMATTED_VALUE") -> list:
        """Valores de un rango de UNA columna como lista ('' si está vacía)."""
        first, last = range_a1.rsplit("!", 1)[-1].split(":")
        size = int(re.sub(r"\D", "", last)) - int(re.sub(r"\D", "", first)) + 1
        rows = self.values(file_id, range_a1, render=render)[0]
        flat = [row[0] if row else "" for row in rows]
        return flat + [""] * (size - len(flat))

    def entered_type(self, file_id: str, a1: str) -> str | None:
        """Tipo del valor ingresado: 'numberValue', 'stringValue', 'formulaValue'..."""
        response = self._x(self.sheets.spreadsheets().get(
            spreadsheetId=file_id, ranges=[a1], includeGridData=True,
            fields="sheets.data.rowData.values.userEnteredValue"))
        try:
            entered = response["sheets"][0]["data"][0]["rowData"][0]["values"][0]["userEnteredValue"]
        except (KeyError, IndexError):
            return None
        return next(iter(entered))

    def set_value(self, file_id: str, a1: str, value) -> None:
        self._x(self.sheets.spreadsheets().values().update(
            spreadsheetId=file_id, range=a1, valueInputOption="RAW", body={"values": [[value]]}))

    def sheet_titles(self, file_id: str) -> list[str]:
        response = self._x(self.sheets.spreadsheets().get(
            spreadsheetId=file_id, fields="sheets.properties.title"))
        return [s["properties"]["title"] for s in response["sheets"]]

    def rename_sheet(self, file_id: str, old: str, new: str) -> None:
        response = self._x(self.sheets.spreadsheets().get(
            spreadsheetId=file_id, fields="sheets.properties(sheetId,title)"))
        sheet_id = next(s["properties"]["sheetId"] for s in response["sheets"]
                        if s["properties"]["title"] == old)
        self._x(self.sheets.spreadsheets().batchUpdate(spreadsheetId=file_id, body={"requests": [
            {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "title": new},
                                       "fields": "title"}}]}))


# ----------------------------------------------------------------------
# Base de datos local (la misma que monta el contenedor)
# ----------------------------------------------------------------------
class E2EDatabase:
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"No existe la base de datos {path}")
        self._path = path

    def _execute(self, sql: str, params: tuple) -> int:
        for attempt in range(10):
            try:
                with sqlite3.connect(self._path, timeout=10) as connection:
                    connection.execute("PRAGMA foreign_keys = ON")
                    return connection.execute(sql, params).lastrowid
            except sqlite3.OperationalError as error:  # base bloqueada por el bot
                if "locked" not in str(error) or attempt == 9:
                    raise
                time.sleep(0.2)
        raise RuntimeError("inalcanzable")

    def add_business(self, name: str, sheets_folder: str, workers_folder: str | None) -> int:
        return self._execute(
            "INSERT INTO businesses (name, sheets_folder_id, workers_folder_id) VALUES (?, ?, ?)",
            (name, sheets_folder, workers_folder),
        )

    def add_admin(self, business_id: int, name: str) -> str:
        phone = "77" + "".join(random.choices("0123456789", k=10))
        self._execute(
            "INSERT INTO business_administrators (business_id, name, phone_number) VALUES (?, ?, ?)",
            (business_id, name, phone),
        )
        return phone

    def delete_business(self, business_id: int) -> None:
        self._execute("DELETE FROM business_administrators WHERE business_id = ?", (business_id,))
        self._execute("DELETE FROM businesses WHERE id = ?", (business_id,))


class Run:
    """Recursos de una corrida E2E: carpetas, negocios y administradores."""

    def __init__(self, google: Google, db: E2EDatabase, stamp: str, root: str,
                 planillas: str, trabajadores: str, business_id: int,
                 no_workers_planillas: str, no_workers_business_id: int):
        self.google = google
        self.db = db
        self.stamp = stamp
        self.root = root
        self.planillas = planillas
        self.trabajadores = trabajadores
        self.business_id = business_id
        self.business_name = f"E2E {stamp}"
        self.no_workers_planillas = no_workers_planillas
        self.no_workers_business_id = no_workers_business_id
        self.extra_businesses: list[int] = []

    def new_business(self, label: str) -> tuple[int, str]:
        """Negocio propio (con su carpeta de planillas) para pruebas que recorren
        TODAS las planillas del negocio, como corregir_saldos."""
        folder = self.google.create_folder(f"planillas-{label}", self.root)
        business_id = self.db.add_business(f"E2E {label} {self.stamp}", folder, self.trabajadores)
        self.extra_businesses.append(business_id)
        return business_id, folder

    def new_admin(self, name: str = "Admin E2E", business_id: int | None = None) -> BotUser:
        phone = self.db.add_admin(business_id or self.business_id, name)
        return BotUser(phone, name)

    # Atajos de verificación
    def planilla(self, name: str, folder: str | None = None) -> str:
        file_id = self.google.planilla(folder or self.planillas, name)
        assert file_id, f"no existe la planilla {name}"
        return file_id

    def worker_files(self) -> dict[str, str]:
        """{nombre: id} de los archivos de trabajadores."""
        files = self.google.children(self.trabajadores)
        names = [name for _, name in files]
        assert len(names) == len(set(names)), f"archivos de trabajador duplicados: {sorted(names)}"
        return {name: file_id for file_id, name in files}

    def worker(self, name: str) -> str:
        files = self.worker_files()
        assert name in files, f"no existe el archivo del trabajador {name!r}: {sorted(files)}"
        return files[name]
