"""
Layout declarativo de la planilla de contabilidad.

Toda la estructura de la plantilla (qué celdas usa cada concepto) se describe
una única vez aquí. Una región se define por su celda contadora, sus columnas
de datos y sus filas válidas.

Los límites de cada región salen de las fórmulas de la plantilla real
(Formato_Planilla / Formato_Trabajadores): escribir fuera de ellos pisaría
otra sección o los totales.
"""
from dataclasses import dataclass

from sheets.a1 import cell_at, column_number, parse_cell, split_sheet

#: Regiones de la planilla diaria, en el orden en que se muestran al usuario.
DAILY_REGION_ATTRS = (
    "expense_region",
    "worker_loan_region",
    "admin_region",
    "withdraw_region",
    "investment_region",
    "cleaning_region",
    "feeding_region",
)


def sheet_prefix(title: str) -> str:
    """Prefijo A1 de una hoja: 'principal' -> "'principal'!" (comillas escapadas)."""
    return "'" + title.replace("'", "''") + "'!"


@dataclass(frozen=True)
class SheetRegion:
    """Región de filas dinámicas de la planilla.

    Attributes:
        label: nombre legible de la sección (para mensajes al usuario).
        counter_cell: celda que almacena la próxima fila libre de la región.
        target_columns: columnas (notación A1, ej. "A:B") donde se escriben
            los datos de cada fila. Puede llevar prefijo de hoja.
        min_row: primera fila válida de la región.
        max_row: última fila válida de la región (inclusive).
        blank: valor "vacío" de cada columna, el que tiene la plantilla
            (ej: la columna de valores del archivo de trabajador trae 0).
    """

    label: str
    counter_cell: str
    target_columns: str
    min_row: int
    max_row: int
    blank: tuple = ()

    @property
    def _prefix_and_columns(self) -> tuple[str, str, str]:
        prefix, columns = split_sheet(self.target_columns)
        first, _, last = columns.partition(":")
        return prefix, first, last or first

    @property
    def width(self) -> int:
        _, first, last = self._prefix_and_columns
        return column_number(last) - column_number(first) + 1

    @property
    def capacity(self) -> int:
        return self.max_row - self.min_row + 1

    @property
    def blank_row(self) -> list:
        values = list(self.blank)[: self.width]
        return values + [""] * (self.width - len(values))

    def row_range(self, row: int) -> str:
        return self.block_range(row, row)

    def moved(self, sheet_prefix: str, row_offset: int) -> "SheetRegion":
        """La misma región en otra hoja y desplazada `row_offset` filas hacia arriba.

        Sirve para leer una hoja archivada de nómina: es una copia de
        "principal" a la que se le borraron las primeras filas.
        """
        _, columns = split_sheet(self.target_columns)
        _, counter = split_sheet(self.counter_cell)
        column, row = parse_cell(counter)
        return SheetRegion(
            label=self.label,
            counter_cell=cell_at(sheet_prefix, column, row - row_offset),
            target_columns=f"{sheet_prefix}{columns}",
            min_row=self.min_row - row_offset,
            max_row=self.max_row - row_offset,
            blank=self.blank,
        )

    def block_range(self, first_row: int, last_row: int) -> str:
        prefix, first, last = self._prefix_and_columns
        return f"{prefix}{first}{first_row}:{last}{last_row}"


@dataclass(frozen=True)
class PlanillaLayout:
    """Mapa completo de la plantilla de planilla diaria."""

    # Celdas fijas del encabezado
    business_name_cell: str = "A2"   # celdas combinadas A2:E2
    admin_name_cell: str = "B6"
    date_cell: str = "B7"

    # Bloque "MANEJO DEL EFECTIVO" (columna B)
    total_expenses_cell: str = "B38"  # TOTAL GASTOS DIA (fórmula)
    day_cash_cell: str = "B39"        # EFECTIVO (lo escribe el comando 'efectivo')
    total_sales_cell: str = "B40"     # TOTAL VENTA (fórmula)
    generated_cash_cell: str = "B42"  # SALDO EFECTIVO: saldo previo / comando 'saldo'
    total_cash_cell: str = "B58"      # SALDO TOTAL (fórmula, se propaga al día siguiente)

    # Regiones de filas dinámicas. Contadores en C135:C141 ("NO TOCAR").
    expense_region: SheetRegion = SheetRegion(
        "compras proveedores", "C135", "A:B", 11, 34)          # B35 = SUM(B11:B34)
    worker_loan_region: SheetRegion = SheetRegion(
        "préstamos a trabajadores", "C136", "C:D", 11, 26)     # D27 = SUM(D11:D26)
    admin_region: SheetRegion = SheetRegion(
        "administrador", "C137", "E:E", 26, 34)                # E35 = SUM(E26:E34)
    withdraw_region: SheetRegion = SheetRegion(
        "retiros", "C138", "C:E", 39, 59)                      # E60 = SUM(E39:E59)
    investment_region: SheetRegion = SheetRegion(
        "inversiones", "C139", "C:D", 29, 34)                  # D35 = SUM(D29:D34)
    cleaning_region: SheetRegion = SheetRegion(
        "aseo", "C140", "E:E", 11, 18)                         # SUM(E10:E18) en B38
    feeding_region: SheetRegion = SheetRegion(
        "alimentación", "C141", "E:E", 20, 24)                 # SUM(E20:E24) en B38

    # ------------------------------------------------------------------
    # Archivo individual de cada trabajador (Formato_Trabajadores)
    # ------------------------------------------------------------------
    # IMPORTANTE: el prefijo "principal!" es obligatorio porque el archivo
    # acumula subhojas de nómina y sin prefijo los rangos podrían escribir
    # en la hoja equivocada.
    worker_main_sheet: str = "principal"
    # Columna A = fecha del préstamo, B = monto (la plantilla trae 0 en B).
    worker_file_region: SheetRegion = SheetRegion(
        "vales", "principal!C123", "principal!A:C", 13, 28, ("", 0, ""))
    worker_business_name_cell: str = "principal!A2"   # celdas combinadas A2:C2
    worker_loan_sum_cell: str = "principal!B30"       # TOTAL = SUM(B13:B29)
    # Filas que se eliminan de la copia archivada al cerrar la nómina.
    worker_archive_deleted_rows: tuple[int, int] = (1, 9)

    @property
    def daily_regions(self) -> tuple[tuple[str, SheetRegion], ...]:
        """(nombre del atributo, región) de cada sección de la planilla diaria."""
        return tuple((attr, getattr(self, attr)) for attr in DAILY_REGION_ATTRS)

    @property
    def worker_archive_offset(self) -> int:
        """Cuántas filas subió todo en una hoja archivada de nómina."""
        first_row, last_row = self.worker_archive_deleted_rows
        return last_row - first_row + 1
