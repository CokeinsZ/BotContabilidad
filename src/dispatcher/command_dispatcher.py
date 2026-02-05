from dispatcher.commands.employees_service import EmployeesService
from dispatcher.commands.expenses_service import ExpensesService
from dispatcher.commands.sheets_service import SheetsService


class CommandDispatcher:
    def __init__(self, drive_service, sheets_service):
        self.drive_service = drive_service
        self.google_sheets_service = sheets_service

        self.sheets_service = SheetsService(self.google_sheets_service, self.drive_service)
        self.cash_service = None
        self.employees_service = EmployeesService(self.sheets_service, self.google_sheets_service)
        self.expenses_service = ExpensesService(self.sheets_service, self.google_sheets_service)

        self.commands = {
            "hoja": self.sheets_service.create_or_select_sheet,
            "h": self.sheets_service.create_or_select_sheet,

            "gasto": self.expenses_service.record_expense,
            "g": self.expenses_service.record_expense,

            "trabajador": self.employees_service.record_employee_payment,
            "trabajadores": self.employees_service.record_employee_payment,
            "t": self.employees_service.record_employee_payment,

            "administrador": self.employees_service.record_admin_payment,
            "admin": self.employees_service.record_admin_payment,
            
        }

    def run(self, full_command: str):
        # Separamos el comando de los argumentos (ej: "gasto 5000 papas")
        parts = full_command.split()
        if not parts: return
        
        cmd = parts[0]
        args = parts[1:]

        action = self.commands.get(cmd)
        if action:
            return action(args)
        else:
            print(f"⚠️ Comando desconocido: {cmd}")