
class SummaryService:
    def __init__(self, sheets_service, google_sheets_service):
        self.sheets_service = sheets_service
        self.google_sheets_service = google_sheets_service

    def generate_summary(self, args: list):
        """
        Genera un resumen de ingresos, gastos y saldo para la planilla activa.
        
        Args:
            args: Lista de argumentos (no se requieren argumentos para este comando).
        """
        if not self.sheets_service.active_sheet_id:
            print("⚠️ No hay una planilla activa. Usa el comando 'hoja' para seleccionar o crear una planilla.")
            return

        sheet_id = self.sheets_service.active_sheet_id
        planilla_cash, total_sells, previous_cash, total_cash = self.google_sheets_service.get_daily_totals(sheet_id)

        return f"""
            Resumen de la planilla:
                - Efectivo del día: {planilla_cash}
                - Ventas totales del día: {total_sells}
                - Efectivo previo: {previous_cash}
                - Efectivo total: {total_cash}
        """