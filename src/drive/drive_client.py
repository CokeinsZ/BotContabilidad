"""
Cliente de bajo nivel para la API de Google Drive.

A diferencia de la versión anterior, ningún método usa variables globales:
la carpeta raíz de planillas (`folder_id`) se recibe en cada llamada, lo que
permite atender a múltiples businesses con un mismo cliente.

Optimización: la búsqueda de una planilla calcula directamente la carpeta del
mes a partir del nombre-fecha (`dd-mm-yyyy` -> `mes-aaaa`), evitando el
recorrido N+1 por todas las carpetas mensuales que hacía la versión anterior.
"""
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth.google_auth_manager import GoogleAuthManager

_MONTH_NAMES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

_FOLDER_MIME = "application/vnd.google-apps.folder"
_SHEET_MIME = "application/vnd.google-apps.spreadsheet"


class DriveClient:
    """Operaciones sobre Google Drive, agnóstico del business (stateless)."""

    def __init__(
        self,
        auth_manager: GoogleAuthManager,
        planilla_template_id: str,
        workers_template_id: str,
    ):
        self._auth_manager = auth_manager
        self._planilla_template_id = planilla_template_id
        self._workers_template_id = workers_template_id
        self._service = None
        self._credentials_used = None

    @property
    def service(self):
        """Construye el servicio de la API de forma perezosa.

        Devuelve None si aún no hay credenciales de Google disponibles.
        Se reconstruye automáticamente si las credenciales cambian (re-login).
        """
        credentials = self._auth_manager.get_credentials()
        if credentials is None:
            return None
        if self._service is None or credentials is not self._credentials_used:
            self._service = build("drive", "v3", credentials=credentials)
            self._credentials_used = credentials
        return self._service

    # ------------------------------------------------------------------
    # Planillas
    # ------------------------------------------------------------------
    def find_sheet_by_name(self, folder_id: str, sheet_name: str) -> str | None:
        """Devuelve el id de la planilla `<sheet_name>` del business, o None.

        Como el nombre es una fecha (`dd-mm-yyyy`), se busca únicamente en la
        carpeta del mes correspondiente: 2 llamadas a la API como máximo.
        """
        month_folder_name = self.month_folder_name_for(sheet_name)
        if month_folder_name is None:
            return None

        month_folder_id = self._find_folder(folder_id, month_folder_name)
        if month_folder_id is None:
            return None

        try:
            query = (
                f"mimeType='{_SHEET_MIME}' and "
                f"name='{sheet_name}' and '{month_folder_id}' in parents and trashed=false"
            )
            response = (
                self.service.files()
                .list(q=query, fields="files(id,name)", pageSize=1)
                .execute()
            )
            files = response.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as error:
            print(f"Error buscando la planilla '{sheet_name}': {error}")
            return None

    def duplicate_template(
        self, folder_id: str, new_name: str
    ) -> tuple[str, str] | None:
        """Duplica la plantilla de planilla dentro de la carpeta mensual del business.

        Crea la carpeta del mes (`mes-aaaa`) si no existe.
        Devuelve (id, nombre) de la copia, o None si falla.
        """
        month_folder_name = self.month_folder_name_for(new_name)
        if month_folder_name is None:
            print(f"Formato de fecha inválido: '{new_name}'. Usa dd-mm-aaaa")
            return None

        month_folder_id = self._find_folder(folder_id, month_folder_name)
        if month_folder_id is None:
            month_folder_id = self._create_folder(folder_id, month_folder_name)
            if month_folder_id is None:
                return None

        return self._copy_file(self._planilla_template_id, new_name, month_folder_id)

    def duplicate_workers_template(
        self, folder_id: str, worker_name: str
    ) -> tuple[str, str] | None:
        """Duplica el Formato_Trabajadores en la carpeta de trabajadores.

        Devuelve (id, nombre) de la copia, o None si falla.
        """
        return self._copy_file(self._workers_template_id, worker_name, folder_id)

    def _copy_file(
        self, template_id: str, new_name: str, parent_folder_id: str
    ) -> tuple[str, str] | None:
        try:
            body = {"name": new_name, "parents": [parent_folder_id]}
            copied_file = (
                self.service.files()
                .copy(fileId=template_id, body=body)
                .execute()
            )
            return copied_file.get("id"), copied_file.get("name")
        except HttpError as error:
            print(f"Error al duplicar el archivo '{new_name}': {error}")
            return None

    # ------------------------------------------------------------------
    # Listados
    # ------------------------------------------------------------------
    def find_daily_sheets(self, folder_id: str, date_str: str) -> list[tuple[str, str]]:
        """Lista (id, nombre) de TODAS las planillas de un día dado.

        Incluye la planilla base (`dd-mm-yyyy`) y las adicionales
        (`dd-mm-yyyy-2`, `dd-mm-yyyy-3`, ...), ordenadas por ordinal.
        """
        month_folder_name = self.month_folder_name_for(date_str)
        if month_folder_name is None:
            return []

        month_folder_id = self._find_folder(folder_id, month_folder_name)
        if month_folder_id is None:
            return []

        candidates = [
            (file_id, name)
            for file_id, name in self.list_files_in_folder(month_folder_id)
            if self._day_ordinal(name, date_str) is not None
        ]
        candidates.sort(key=lambda item: self._day_ordinal(item[1], date_str))
        return candidates

    def list_files_in_folder(self, folder_id: str) -> list[tuple[str, str]]:
        """Lista (id, nombre) de todos los spreadsheets de una carpeta."""
        files: list[tuple[str, str]] = []
        try:
            page_token = None
            while True:
                query = (
                    f"mimeType='{_SHEET_MIME}' and "
                    f"'{folder_id}' in parents and trashed=false"
                )
                response = (
                    self.service.files()
                    .list(
                        q=query,
                        fields="nextPageToken, files(id,name)",
                        pageSize=100,
                        pageToken=page_token,
                    )
                    .execute()
                )
                files.extend((f["id"], f["name"]) for f in response.get("files", []))
                page_token = response.get("nextPageToken")
                if not page_token:
                    break
            return files
        except HttpError as error:
            print(f"Error listando archivos de la carpeta {folder_id}: {error}")
            return []

    @staticmethod
    def _day_ordinal(name: str, date_str: str) -> int | None:
        """Ordinal de la planilla dentro del día: base=1, `-N`=N. None si no aplica."""
        if name == date_str:
            return 1
        prefix = f"{date_str}-"
        if name.startswith(prefix):
            suffix = name[len(prefix):]
            if suffix.isdigit():
                return int(suffix)
        return None

    # ------------------------------------------------------------------
    # Carpetas
    # ------------------------------------------------------------------
    def _find_folder(self, parent_id: str, folder_name: str) -> str | None:
        try:
            query = (
                f"mimeType='{_FOLDER_MIME}' and "
                f"name='{folder_name}' and '{parent_id}' in parents and trashed=false"
            )
            response = (
                self.service.files()
                .list(q=query, fields="files(id,name)", pageSize=1)
                .execute()
            )
            files = response.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as error:
            print(f"Error buscando la carpeta '{folder_name}': {error}")
            return None

    def _create_folder(self, parent_id: str, folder_name: str) -> str | None:
        try:
            metadata = {
                "name": folder_name,
                "mimeType": _FOLDER_MIME,
                "parents": [parent_id],
            }
            folder = (
                self.service.files()
                .create(body=metadata, fields="id")
                .execute()
            )
            return folder.get("id")
        except HttpError as error:
            print(f"Error creando la carpeta '{folder_name}': {error}")
            return None

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def month_folder_name_for(date_str: str) -> str | None:
        """Convierte `dd-mm-yyyy` en el nombre de carpeta `mes-aaaa`."""
        try:
            date = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            return None
        return f"{_MONTH_NAMES[date.month - 1]}-{date.year}"
