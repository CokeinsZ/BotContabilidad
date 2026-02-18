from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class PlanillaSheetService:
    def __init__(self, creds):
        self.creds = creds
        self.service = build('sheets', 'v4', credentials=self.creds)

    def set_generated_cash(self, sheet_id: str, amount: int):
        try:
            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='B42',
                valueInputOption='RAW',
                body={'values': [[amount]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el saldo generado: {error}")
            return False

    def append_expense(self, spreadsheet_id: str, data: list):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='C123'
            ).execute().get('values', [[]])[0][0]
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'A{last_row}:B{last_row}',
                valueInputOption='RAW',
                body={'values': [data]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_row(last_row, spreadsheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el gasto: {error}")
            return False

    def append_cash(self, sheet_id, row_data):
        try:
            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='B39',
                valueInputOption='RAW',
                body={'values': [[row_data]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el efectivo: {error}")

    def add_worker_payment(self, sheet_id: str, data: list):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C124'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'C{last_row}:D{last_row}',
                valueInputOption='RAW',
                body={'values': [data]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_worker(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el pago al trabajador: {error}")
            return False

    def add_admin_expense(self, sheet_id: str, data: int):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C125'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'E{last_row}',
                valueInputOption='RAW',
                body={'values': [[data]]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_admin_expense(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el gasto administrativo: {error}")
            return False

    def add_investment(self, sheet_id: str, data: list):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C127'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'C{last_row}:D{last_row}',
                valueInputOption='RAW',
                body={'values': [data]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_investment(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar la inversión: {error}")
            return False

    def add_withdraw(self, sheet_id: str, data: list):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C126'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'C{last_row}:E{last_row}',
                valueInputOption='RAW',
                body={'values': [[data[0], "", data[1]]]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_withdraw(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el retiro: {error}")
        return False


    def add_cleaning_expense(self, sheet_id: str, data: int):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C128'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'E{last_row}',
                valueInputOption='RAW',
                body={'values': [[data]]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_cleaning_expense(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el gasto de limpieza: {error}")
            return False

    def add_feeding_expense(self, sheet_id: str, data: int):
        try:
            last_row = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='C129'
            ).execute().get('values', [[]])[0][0]

            result = self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'E{last_row}',
                valueInputOption='RAW',
                body={'values': [[data]]}
            ).execute()
            if result.get('updatedCells'):
                self.increase_last_feeding_expense(last_row, sheet_id)
                return True
        except HttpError as error:
            print(f"Ocurrió un error al agregar el gasto de alimentación: {error}")
            return False



    def get_daily_totals(self, sheet_id: str):
        try:
            values = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='B38:B46'
            ).execute().get('values', [[]])

            print(f"Totales obtenidos de la planilla {sheet_id}: {values}")

            def get_value_at(index, default="0"):
                if index < len(values) and values[index]:
                    return values[index][0]
                return default

            total_expenses = get_value_at(0)
            planilla_cash = get_value_at(1)
            total_sells = get_value_at(2)
            previous_cash = get_value_at(4)
            total_cash = get_value_at(8)
            return total_expenses, planilla_cash, total_sells, previous_cash, total_cash
        except HttpError as error:
            print(f"Ocurrió un error al obtener los totales: {error}")
            return None

    def get_name_by_id(self, spreadsheet_id: str):
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            return spreadsheet.get('properties', {}).get('title', None)
        except HttpError as error:
            print(f"Error obteniendo el nombre de la hoja: {error}")
            return None

    def get_value(self, spreadsheet_id: str, range_a1: str):
        try:
            values = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_a1
            ).execute().get('values', [[]])
            if values and values[0]:
                return values[0][0]
            return None
        except HttpError as error:
            print(f"Error obteniendo valor {range_a1}: {error}")
            return None

    def clear_range(self, spreadsheet_id: str, range_a1: str):
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_a1,
                body={}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error limpiando rango {range_a1}: {error}")
            return False

    def update_single_value(self, spreadsheet_id: str, range_a1: str, value):
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_a1,
                valueInputOption='RAW',
                body={'values': [[value]]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error actualizando celda {range_a1}: {error}")
            return False

    def increase_last_row(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C123',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila: {error}")
        return None

    def undo_expense(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C123')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 11:
                return False
            if not self.clear_range(spreadsheet_id, f'A{target_row}:B{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C123', target_row)
        except ValueError:
            return False

    def undo_shift_cash(self, spreadsheet_id: str, previous_value):
        value = previous_value if previous_value is not None else 0
        return self.update_single_value(spreadsheet_id, 'B39', value)

    def increase_last_worker(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C124',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila del trabajador: {error}")
        return None
    
    def undo_worker_payment(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C124')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 11:
                return False
            if not self.clear_range(spreadsheet_id, f'C{target_row}:D{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C124', target_row)
        except ValueError:
            return False
        
    def increase_last_admin_expense(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C125',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila del gasto administrativo: {error}")
        return None
    
    def undo_admin_expense(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C125')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 26:
                return False
            if not self.clear_range(spreadsheet_id, f'E{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C125', target_row)
        except ValueError:
            return False
        
    def increase_last_withdraw(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C126',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila del retiro: {error}")
        return None
    
    def undo_withdraw(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C126')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 39:
                return False
            if not self.clear_range(spreadsheet_id, f'C{target_row}:E{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C126', target_row)
        except ValueError:
            return False

    def undo_generated_cash(self, spreadsheet_id: str, previous_value):
        value = previous_value if previous_value is not None else ''
        return self.update_single_value(spreadsheet_id, 'B42', value)

    def increase_last_investment(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C127',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila de la inversión: {error}")
        return None
    
    def undo_investment(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C127')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 29:
                return False
            if not self.clear_range(spreadsheet_id, f'C{target_row}:D{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C127', target_row)
        except ValueError:
            return False
        
    def increase_last_cleaning_expense(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C128',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila del gasto de limpieza: {error}")
        return None
    
    def undo_cleaning_expense(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C128')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 11:
                return False
            if not self.clear_range(spreadsheet_id, f'E{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C128', target_row)
        except ValueError:
            return False
        
    def increase_last_feeding_expense(self, old_value, spreadsheet_id: str):
        try:
            last_row = int(old_value) + 1
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='C129',
                valueInputOption='RAW',
                body={'values': [[last_row]]}
            ).execute()
            if result.get('updatedCells'):
                return True
        except HttpError as error:
            print(f"Ocurrió un error al incrementar la fila del gasto de alimentación: {error}")
        return None
    
    def undo_feeding_expense(self, spreadsheet_id: str):
        current = self.get_value(spreadsheet_id, 'C129')
        if current is None:
            return False
        try:
            target_row = int(current) - 1
            if target_row < 20:
                return False
            if not self.clear_range(spreadsheet_id, f'E{target_row}'):
                return False
            return self.update_single_value(spreadsheet_id, 'C129', target_row)
        except ValueError:
            return False