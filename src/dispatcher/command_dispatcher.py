from dispatcher.commands.cash_service import CashService
from dispatcher.commands.employees_service import EmployeesService
from dispatcher.commands.expenses_service import ExpensesService
from dispatcher.commands.sheets_service import SheetsService
from dispatcher.commands.summary_service import SummaryService
from dispatcher.commands.undo_service import UndoService


class CommandDispatcher:
    def __init__(self, drive_service, sheets_service):
        self.drive_service = drive_service
        self.google_sheets_service = sheets_service

        self.sheets_service = SheetsService(self.google_sheets_service, self.drive_service)
        self.cash_service = CashService(self.sheets_service, self.google_sheets_service)
        self.employees_service = EmployeesService(self.sheets_service, self.google_sheets_service)
        self.expenses_service = ExpensesService(self.sheets_service, self.google_sheets_service)
        self.summary_service = SummaryService(self.sheets_service, self.google_sheets_service)
        self.undo_service = UndoService(self.google_sheets_service)

        self.commands = {
            "hoja": self.sheets_service.create_or_select_sheet,
            "planilla": self.sheets_service.create_or_select_sheet,
            "h": self.sheets_service.create_or_select_sheet,

            "gasto": self.expenses_service.record_expense,
            "g": self.expenses_service.record_expense,

            "trabajador": self.employees_service.record_employee_payment,
            "trabajadores": self.employees_service.record_employee_payment,
            "t": self.employees_service.record_employee_payment,

            "administrador": self.employees_service.record_admin_payment,
            "admin": self.employees_service.record_admin_payment,

            "retiro": self.cash_service.record_withdrawal,
            "r": self.cash_service.record_withdrawal,

            "saldo": self.cash_service.record_balance,
            "saldos": self.cash_service.record_balance,
            "s": self.cash_service.record_balance,

            "efectivo": self.cash_service.record_cash,
            "e": self.cash_service.record_cash,

            "terminar_dia": self.summary_service.generate_summary,
            "resumen": self.summary_service.generate_summary,

            "instrucciones": self.list_commands,
            "i": self.list_commands,
            "help": self.list_commands,

            "deshacer": self.undo_service.undo_last_command,
            "undo": self.undo_service.undo_last_command,
            
        }

    def run(self, full_command: str):
        # Separamos el comando de los argumentos (ej: "gasto 5000 papas")
        parts = full_command.split()
        if not parts: return
        
        cmd = parts[0]
        args = parts[1:]

        print(f"Ejecutando comando: {cmd} con argumentos: {args}")

        action = self.commands.get(cmd)
        if action:
            self.undo_service.store_last_command(cmd, args, self.sheets_service.active_sheet_id)
            return action(args)
        else:
            return(f"⚠️ Comando desconocido: {cmd}")

    def list_commands(self, args):
        return """
            Bienvenido al Bot de Contabilidad. \n
            Link a la carpeta: https://drive.google.com/drive/folders/1XGiZbI4M4OVpGNZT-p205fKvjJ5Zf7sC?usp=sharing \n
            Instrucciones de uso:\n
            1. Seleccionar o crear una hoja, usando el comando: \n
             'hoja <fecha>' \n
            2. Ejecutar la acción que desees: \n
             2.1. Para agregar un gasto: \n
                'gasto <monto> <descripcion>'\n

             2.2. Para agregar un pago a trabajadores: \n
                'trabajador <monto> <nombre>'\n

             2.3. Para agregar un vale del administrador: \n
                'administrador <monto>'\n

             2.4. Para agregar un retiro de efectivo: \n
                'retiro <monto> <descripcion>'\n

             2.5. Para registrar el saldo de efectivo: \n
                'saldo <monto>'\n

             2.6. Para agregar un el efectivo del dia: \n
                'efectivo <monto>'\n

             2.7. Para terminar el dia, y actualizar la hoja de resumen de ventas: \n
             'terminar_dia' \n

             2.8. Para ver las instrucciones de uso: \n
                'instrucciones' \n
                
             2.9. Para deshacer el ultimo comando: \n
                'deshacer' \n

            3. Al finalizar, ejecutar el comando 'terminar_dia' para ver el resumen de ventas. \n
        
            ¡Gracias por usar el Bot de Contabilidad!
        """
