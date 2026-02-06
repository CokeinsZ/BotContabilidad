
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
            print("⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla.")
            return

        if len(args) < 2:
            print("⚠️ Debes proporcionar el monto y la descripción del retiro.")
            return

        try:
            amount = float(args[0])
            description = ' '.join(args[1:])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.add_withdraw(sheet_id, args)
            print(f"Retiro registrado: {amount} - {description}")

        except ValueError:
            print("⚠️ El monto del retiro debe ser un número válido.")

    def record_balance(self, args: list):
        """
        Registra el saldo de efectivo en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del saldo
        """
        if not self.sheets_service.active_sheet_id:
            print("⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla.")
            return

        if len(args) < 1:
            print("⚠️ Debes proporcionar el monto del saldo.")
            return

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.set_generated_cash(sheet_id, args)
            print(f"Saldo registrado: {amount}")

        except ValueError:
            print("⚠️ El monto del saldo debe ser un número válido.")
        
    def record_cash(self, args: list):
        """
        Registra el efectivo del día en la planilla activa.
        
        Args:
            args: Lista de argumentos, donde el primer elemento es el monto del efectivo
        """
        if not self.sheets_service.active_sheet_id:
            print("⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla.")
            return

        if len(args) < 1:
            print("⚠️ Debes proporcionar el monto del efectivo.")
            return

        try:
            amount = float(args[0])

            sheet_id = self.sheets_service.active_sheet_id
            self.sheets_service.google_sheets_service.append_cash(sheet_id, args)
            print(f"Efectivo registrado: {amount}")

        except ValueError:
            print("⚠️ El monto del efectivo debe ser un número válido.")