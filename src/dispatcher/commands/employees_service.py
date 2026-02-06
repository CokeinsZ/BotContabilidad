

class EmployeesService:
    def __init__(self, sheets_service, google_sheets_service):
        self.sheets_service = sheets_service
        self.google_sheets_service = google_sheets_service

    def record_employee_payment(self, args: list):
        """
        Registra el pago a un trabajador en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del pago
                  y el resto es el nombre del trabajador.
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y el nombre del trabajador."

        try:
            amount = float(args[0])
            description = ' '.join(args[1:])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_worker_payment(sheet_id, args)
            return f"Pago registrado: {amount} - {description}"

        except ValueError:
            return "⚠️ El monto del pago debe ser un número válido."

    def record_admin_payment(self, args: list):
        """
        Registra un pago o vale al administrador en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del pago
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 1:
            return "⚠️ Debes proporcionar el monto del pago."

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_admin_expense(sheet_id, args)
            return f"Pago administrativo registrado: {amount}"

        except ValueError:
            return "⚠️ El monto del pago debe ser un número válido."