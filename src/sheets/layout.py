"""
Layout declarativo de la planilla de contabilidad.

Toda la estructura de la plantilla (qué celdas usa cada concepto) se describe
una única vez aquí. Esto elimina la duplicación masiva de métodos
`add_*` / `increase_*` / `undo_*` que existía antes: una región se define por
su celda contadora, sus columnas de datos y su fila mínima.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SheetRegion:
    """Región de filas dinámicas de la planilla.

    Attributes:
        counter_cell: celda que almacena la próxima fila libre de la región.
        target_columns: columnas (notación A1, ej. "A:B") donde se escriben
            los datos de cada fila.
        min_row: primera fila válida de la región (límite para deshacer).
    """

    counter_cell: str
    target_columns: str
    min_row: int

    def row_range(self, row: int) -> str:
        return f"{self.target_columns.split(':')[0]}{row}:{self.target_columns.split(':')[-1]}{row}"


@dataclass(frozen=True)
class PlanillaLayout:
    """Mapa completo de la plantilla de planilla diaria."""

    # Celdas fijas del encabezado / totales
    business_name_cell: str = "A2"   # celdas combinadas A2:E2
    admin_name_cell: str = "B6"
    date_cell: str = "B7"

    day_cash_cell: str = "B39"       # efectivo del día
    generated_cash_cell: str = "B42" # saldo de caja registrado / saldo previo
    total_cash_cell: str = "B46"     # saldo total (se propaga al día siguiente)
    totals_range: str = "B38:B46"    # bloque de totales para el resumen

    # Regiones de filas dinámicas
    expense_region: SheetRegion = SheetRegion("C123", "A:B", 11)
    # Préstamos a trabajadores (no pagos: el dinero se descuenta luego)
    worker_loan_region: SheetRegion = SheetRegion("C124", "C:D", 11)
    admin_region: SheetRegion = SheetRegion("C125", "E:E", 26)
    withdraw_region: SheetRegion = SheetRegion("C126", "C:E", 39)
    investment_region: SheetRegion = SheetRegion("C127", "C:D", 29)
    cleaning_region: SheetRegion = SheetRegion("C128", "E:E", 11)
    feeding_region: SheetRegion = SheetRegion("C129", "E:E", 20)

    # Región del archivo individual de cada trabajador (Formato_Trabajadores):
    # columna A = fecha del préstamo, columna B = monto. Mismo mecanismo de
    # contador en C123 que las planillas.
    # IMPORTANTE: el prefijo "principal!" es obligatorio porque el archivo
    # acumula subhojas de nómina y sin prefijo los rangos podrían escribir
    # en la hoja equivocada.
    worker_file_region: SheetRegion = SheetRegion("principal!C123", "principal!A:B", 1)
