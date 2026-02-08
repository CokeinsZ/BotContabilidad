
from config import ADMIN_NAME

class SheetsService:
    def __init__(self, google_sheets_service, drive_service):
        self.google_sheets_service = google_sheets_service
        self.drive_service = drive_service

        self.active_sheet_id = None

    def create_or_select_sheet(self, args):
        """
        Crea o selecciona una planilla según el argumento dado.

        Args:
            args: Lista de argumentos, donde el primer elemento es el nombre de la planilla.
        """
        if not args:
            return ("⚠️ Debes proporcionar el nombre de la planilla.")

        sheet_name = args[0]

        sheet = self.drive_service.get_planilla_sheet_by_name(sheet_name)
        if sheet:
            self.active_sheet_id = sheet
            return f"Planilla '{sheet_name}' seleccionada."

        id, name = self.drive_service.duplicate_planilla_spreadsheet(sheet_name)
        if id is None: return (f"⚠️ No se pudo crear o encontrar la planilla: '{sheet_name}'.")
            
        self.active_sheet_id = id

        update_date_result = self.update_date(sheet_name)
        if update_date_result.startswith("⚠️"):
            return update_date_result
        
        update_admin_result = self.update_admin_name()
        if update_admin_result.startswith("⚠️"):
            return update_admin_result

        splits = name.rsplit('-')
        previous_day_day = str(int(splits[0])-1) if (int(splits[0])-1) > 10 else f"0{int(splits[0])-1}"
        previous_day_month = splits[1]
        previous_day_year = splits[2]
        m = self._load_previous_balance(f"{previous_day_day}-{previous_day_month}-{previous_day_year}")
        if m != 0: return m + f"\n\nPlanilla '{sheet_name}' seleccionada."

        return f"Planilla '{sheet_name}' seleccionada."

    def update_date(self, date_str):
        if not self.active_sheet_id:
            return ("⚠️ No hay una planilla activa para actualizar la fecha.")
        self.google_sheets_service.update_single_value(self.active_sheet_id, 'B7', date_str)
        return f"Fecha de la planilla actualizada a {date_str}."

    def update_admin_name(self):
        if not self.active_sheet_id:
            return ("⚠️ No hay una planilla activa para actualizar el nombre del administrador.")
        self.google_sheets_service.update_single_value(self.active_sheet_id, 'B6', ADMIN_NAME)
        return f"Nombre del administrador actualizado a {ADMIN_NAME}."

    def _load_previous_balance(self, previous_day_name):
        """Carga el balance de la planilla del día anterior si existe."""
        previous_sheet_id = self.drive_service.get_planilla_sheet_by_name(previous_day_name)
        if previous_sheet_id:
            balance = self.google_sheets_service.get_value(previous_sheet_id, 'B46')
            if balance is None:
                balance = 0
            self.google_sheets_service.update_single_value(self.active_sheet_id, 'B42', balance)
            return 0
        else:
            return (f"No existe una planilla para el día anterior: '{previous_day_name}', \npor lo tanto no se pudo cargar el balance anterior.")
        return 0