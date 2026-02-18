
class ExpensesService:
    def __init__(self, sheets_service, google_sheets_service):
        self.sheets_service = sheets_service
        self.google_sheets_service = google_sheets_service

    def record_expense(self, args):
        """
        Registra un gasto en la planilla activa.

        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del gasto
                  y el resto es la descripción del gasto.
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y la descripción del gasto."

        try:
            amount = float(args[0])
            description = ' '.join(args[1:])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.append_expense(sheet_id, [description, amount])
            return f"Gasto registrado: {amount} - {description}"

        except ValueError:
            return "⚠️ El monto del gasto debe ser un número válido."
        
    def record_cleaning_expense(self, args):
        """
        Registra un gasto de limpieza en la planilla activa.

        Args:
            args: Lista de argumentos, donde el elemento es el monto del gasto
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 1:
            return "⚠️ Debes proporcionar el monto del gasto."

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_cleaning_expense(sheet_id, amount)
            return f"Gasto de limpieza registrado: {amount}"

        except ValueError:
            return "⚠️ El monto del gasto debe ser un número válido."
        
    def record_feeding_expense(self, args):
        """
        Registra un gasto de alimentación en la planilla activa.

        Args:
            args: Lista de argumentos, donde el elemento es el monto del gasto
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 1:
            return "⚠️ Debes proporcionar el monto del gasto."

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_feeding_expense(sheet_id, amount)
            return f"Gasto de alimentación registrado: {amount}"

        except ValueError:
            return "⚠️ El monto del gasto debe ser un número válido."