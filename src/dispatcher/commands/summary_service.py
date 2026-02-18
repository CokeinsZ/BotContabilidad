
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
        totals = self.google_sheets_service.get_daily_totals(sheet_id)
        if not totals:
            return "⚠️ No se pudieron obtener los totales de la planilla."
        total_expenses, planilla_cash, total_sells, previous_cash, total_cash = totals

        return f"""
            Link a la planilla: "https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"

            Resumen de la planilla:
                - Gastos totales del día: {total_expenses}
                - Efectivo del día: {planilla_cash}
                - Ventas totales del día: {total_sells}
                - Saldo previo: {previous_cash}
                - Saldo total: {total_cash}
        """