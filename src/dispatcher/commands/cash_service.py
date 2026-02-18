
class CashService:
    def __init__(self, sheets_service, google_sheets_service):
        self.sheets_service = sheets_service
        self.google_sheets_service = google_sheets_service

    def record_withdrawal(self, args: list):
        """
        Registra un retiro de efectivo en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del retiro
                  y el resto es la descripción del retiro.
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y la descripción del retiro."

        try:
            amount = float(args[0])
            description = ' '.join(args[1:])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_withdraw(sheet_id, [description, amount])
            return f"Retiro registrado: {amount} - {description}"

        except ValueError:
            return "⚠️ El monto del retiro debe ser un número válido."

    def record_balance(self, args: list):
        """
        Registra el saldo de efectivo en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del saldo
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 1:
            return "⚠️ Debes proporcionar el monto del saldo."

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.set_generated_cash(sheet_id, amount)
            return f"Saldo registrado: {amount}"

        except ValueError:
            return "⚠️ El monto del saldo debe ser un número válido."
        
    def record_cash(self, args: list):
        """
        Registra el efectivo del día en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del efectivo
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 1:
            return "⚠️ Debes proporcionar el monto del efectivo."

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.append_cash(sheet_id, amount)
            return f"Efectivo registrado: {amount}"

        except ValueError:
            return "⚠️ El monto del efectivo debe ser un número válido."
        
    def record_investment(self, args: list):
        """
        Registra una inversión en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto de la inversión
                  y el resto es la descripción de la inversión.
        """
        if not self.sheets_service.active_sheet_id:
            return "⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla."

        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y la descripción de la inversión."

        try:
            amount = float(args[0])
            description = ' '.join(args[1:])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_investment(sheet_id, [description, amount])
            return f"Inversión registrada: {amount} - {description}"

        except ValueError:
            return "⚠️ El monto de la inversión debe ser un número válido." 