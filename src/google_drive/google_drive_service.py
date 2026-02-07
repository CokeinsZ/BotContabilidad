from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import MASTER_FOLDER_ID, PLANILLA_SHEETS_FOLDER_ID, PLANILLA_TEMPLATE_ID
from datetime import datetime


class DriveService:
    def __init__(self, creds):
        self.creds = creds
        self.service = build('drive', 'v3', credentials=self.creds)

    def duplicate_planilla_spreadsheet(self, new_name: str):
        """Duplica la planilla template dentro de la carpeta mensual correspondiente.
        """

        # 1. Validar y parsear fecha
        try:
            fecha = datetime.strptime(new_name, "%d-%m-%Y")
        except ValueError:
            print(f"Formato de fecha inválido: '{new_name}'. Usa dd-mm-aaaa")
            return None

        # 2. Mes en letras español
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        folder_name = f"{meses[fecha.month - 1]}-{fecha.year}"

        # 3. Buscar o crear carpeta
        folder_id = self.get_planilla_month_folder_id(folder_name)
        if folder_id is None:
            folder_id = self.create_planilla_month_folder(folder_name)

        # 4. Copiar template dentro de la carpeta mensual
        try:
            body = {'name': new_name, 'parents': [folder_id]}
            copied_file = self.service.files().copy(fileId=PLANILLA_TEMPLATE_ID, body=body).execute()
            return copied_file.get('id'), copied_file.get('name')
        except HttpError as error:
            print(f"Ocurrió un error al duplicar la planilla: {error}")
            return None
        
    def get_planilla_sheet_by_name(self, sheet_name: str) -> str | None:
        """Devuelve el id de la planilla con nombre dado, o None si no existe.
        
        Busca en todas las carpetas dentro de PLANILLA_SHEETS_FOLDER_ID.
        """
        try:
            folder_query = (
                "mimeType='application/vnd.google-apps.folder' and "
                f"'{PLANILLA_SHEETS_FOLDER_ID}' in parents and trashed=false"
            )

            page_token = None
            while True:
                folder_res = self.service.files().list(
                    q=folder_query,
                    fields="nextPageToken, files(id,name)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()

                folders = folder_res.get('files', [])
                for folder in folders:
                    folder_id = folder['id']
                    sheet_query = (
                        "mimeType='application/vnd.google-apps.spreadsheet' and "
                        f"name='{sheet_name}' and '{folder_id}' in parents and trashed=false"
                    )
                    sheet_res = self.service.files().list(
                        q=sheet_query,
                        fields="files(id,name)",
                        pageSize=1
                    ).execute()
                    sheet_files = sheet_res.get('files', [])
                    if sheet_files:
                        return sheet_files[0]['id']

                page_token = folder_res.get('nextPageToken')
                if not page_token:
                    break

            return None
        except HttpError as error:
            print(f"Ocurrió un error buscando la planilla '{sheet_name}': {error}")
            return None

    def get_planilla_month_folder_id(self, folder_name: str) -> str | None:
        """Devuelve el id de la carpeta mensual si existe, sino None."""
        try:
            query = (
                "mimeType='application/vnd.google-apps.folder' and "
                f"name='{folder_name}' and '{PLANILLA_SHEETS_FOLDER_ID}' in parents and trashed=false"
            )
            res = self.service.files().list(q=query, fields="files(id,name)", pageSize=1).execute()
            files = res.get('files', [])
            if files:
                return files[0]['id']
            return None
        except HttpError as error:
            print(f"Ocurrió un error buscando la carpeta '{folder_name}': {error}")
            return None
        
    def get_latest_planilla_folders(self, n=1):
        """Return the n most recently created subfolders within PLANILLA_SHEETS_FOLDER_ID.
        """
        try:
            folder_query = (
                f"mimeType='application/vnd.google-apps.folder' and '{PLANILLA_SHEETS_FOLDER_ID}' in parents and trashed=false"
            )
            folder_results = self.service.files().list(
                q=folder_query,
                orderBy="createdTime desc",
                pageSize=n,
                fields="files(id,name,createdTime)"
            ).execute()

            return folder_results.get('files', [])
        except HttpError as error:
            print(f"Ocurrió un error: {error}")
            return []

    def create_planilla_month_folder(self, folder_name: str) -> str | None:
        """Crea una carpeta dentro de PLANILLA_SHEETS_FOLDER_ID con nombre dado.

        Params:
            folder_name: Ej. 'septiembre-2025'

        Returns:
            id de la carpeta creada o None en caso de error.
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [PLANILLA_SHEETS_FOLDER_ID]
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
        except HttpError as error:
            print(f"Ocurrió un error creando la carpeta '{folder_name}': {error}")
            return None

    def list_recent_planilla_spreadsheets(self):
        """Return all spreadsheets contained in the two most recently created subfolders.
        """
        try:
            recent_folders = self.get_latest_planilla_folders(n=2)

            if not recent_folders:
                # Fallback: si no hay carpetas, devolver vacío (lista) para consistencia
                print("No se encontraron carpetas recientes.")
                return []

            all_spreadsheets: list[list[str, str]] = []

            # Para cada carpeta (ya en orden descendente), listar sus spreadsheets
            for folder in recent_folders:
                folder_id = folder['id']
                sheets_query = (
                    f"mimeType='application/vnd.google-apps.spreadsheet' and '{folder_id}' in parents and trashed=false"
                )
                sheet_results = self.service.files().list(
                    q=sheets_query,
                    pageSize=31,
                    fields="files(id,name)"
                ).execute()
                sheets = sheet_results.get('files', [])
                for sheet in sheets:
                    all_spreadsheets.append([sheet['name'], sheet['id']])

            return all_spreadsheets
        except HttpError as error:
            print(f"Ocurrió un error: {error}")
            return {}
