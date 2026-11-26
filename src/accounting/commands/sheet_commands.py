"""Comandos para crear o seleccionar planillas diarias."""
from datetime import datetime, timedelta

from accounting.commands.base import Command, CommandContext
from accounting.sheet_naming import (
    MAX_DAILY_SHEETS,
    ORDINAL_WORDS,
    base_date_of,
    sheet_name_for,
)
from config.clock import DATE_FORMAT, today_str
from config.log import log_warning


def _initialize_new_sheet(
    ctx: CommandContext, sheet_id: str, date_str: str, previous_sheet_id: str | None
) -> tuple[bool, str | None]:
    """Inicializa una planilla recién creada con UNA escritura por lotes.

    Escribe: nombre del business (A2), administrador (B6), fecha (B7) y, si
    hay planilla previa, su saldo total (B58) como saldo de caja (B42).

    El saldo se lee SIN formato (número): leer "$1.234.567" y escribirlo con
    RAW dejaba texto en B42 y rompía la fórmula del saldo total.

    Devuelve (éxito, advertencia para el usuario o None).
    """
    layout = ctx.sheets.layout
    updates = {
        layout.business_name_cell: [[ctx.business.name]],
        layout.admin_name_cell: [[ctx.administrator.name]],
        layout.date_cell: [[date_str]],
    }
    warning = None
    if previous_sheet_id:
        previous_balance = ctx.sheets.get_value(previous_sheet_id, layout.total_cash_cell)
        if previous_balance is None or previous_balance == "":
            previous_balance = 0
        if isinstance(previous_balance, bool) or not isinstance(previous_balance, (int, float)):
            log_warning(
                "saldo total de la planilla anterior no es numérico",
                f"previous_sheet_id={previous_sheet_id} cell={layout.total_cash_cell} "
                f"value={previous_balance!r}",
            )
            warning = (
                f"⚠️ El saldo total de la planilla anterior no es un número "
                f"({previous_balance!r}); el saldo de caja quedó en 0."
            )
            previous_balance = 0
        updates[layout.generated_cash_cell] = [[previous_balance]]
    return ctx.sheets.set_values(sheet_id, updates), warning


class SelectSheetCommand(Command):
    """`hoja <dd-mm-aaaa>`: selecciona o crea la PRIMERA planilla del día.

    Al crearla, el saldo de caja (B42) se toma del saldo total (B58) de la
    planilla MÁS ALTA del día anterior (si ese día hubo varias planillas, se
    usa la última: "dd-mm-yyyy-3" tiene prioridad sobre "dd-mm-yyyy-2", etc.).
    """

    name = "hoja"
    aliases = ("planilla", "h")

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        if not args:
            return "⚠️ Debes proporcionar el nombre de la planilla."

        sheet_name = args[0]
        try:
            current_date = datetime.strptime(sheet_name, DATE_FORMAT)
        except ValueError:
            return f"⚠️ Formato de fecha inválido: '{sheet_name}'. Usa dd-mm-aaaa."

        folder_id = ctx.business.sheets_folder_id

        # 1. Si ya existe, solo se selecciona (2 llamadas a Drive como máximo).
        existing_id = ctx.drive.find_sheet_by_name(folder_id, sheet_name)
        if existing_id:
            ctx.session.set_active_sheet(existing_id, sheet_name)
            return f"Planilla '{sheet_name}' seleccionada."

        # 2. Crear duplicando la plantilla en la carpeta del mes.
        duplicated = ctx.drive.duplicate_template(folder_id, sheet_name)
        if duplicated is None:
            log_warning(
                "comando 'hoja' no pudo crear la planilla",
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"folder_id={folder_id} sheet_name={sheet_name!r} "
                f"-> ver log previo de DriveClient",
            )
            return f"⚠️ No se pudo crear o encontrar la planilla: '{sheet_name}'."
        sheet_id, _ = duplicated

        # 3. Saldo previo: planilla MÁS ALTA del día anterior.
        previous_day_name = (current_date - timedelta(days=1)).strftime(DATE_FORMAT)
        previous_day_sheets = ctx.drive.find_daily_sheets(folder_id, previous_day_name)
        previous_sheet_id = previous_day_sheets[-1][0] if previous_day_sheets else None

        # 4. Inicializar la planilla nueva con una sola escritura por lotes.
        ok, warning = _initialize_new_sheet(ctx, sheet_id, sheet_name, previous_sheet_id)
        if not ok:
            log_warning(
                "comando 'hoja' creó la planilla pero no pudo inicializarla",
                f"business_id={ctx.business.id} sheet_id={sheet_id} "
                f"sheet_name={sheet_name!r} previous_sheet_id={previous_sheet_id} "
                f"-> ver log previo de SheetsClient",
            )
            return f"⚠️ La planilla '{sheet_name}' se creó pero no pudo inicializarse."

        ctx.session.set_active_sheet(sheet_id, sheet_name)

        message = f"Planilla '{sheet_name}' seleccionada."
        if previous_sheet_id is None:
            message = (
                f"No existe una planilla para el día anterior: '{previous_day_name}',"
                f"\npor lo tanto no se pudo cargar el balance anterior.\n\n{message}"
            )
        return f"{warning}\n\n{message}" if warning else message


class AdditionalSheetCommand(Command):
    """`segunda planilla` / `2 planilla` / ...: planillas adicionales del día.

    La planilla N de un día toma como saldo de caja (B42) el saldo total
    (B58) de la planilla N-1 de ese mismo día. La fecha se toma de la
    planilla activa de la sesión (o del día de hoy si no hay ninguna), y
    puede indicarse explícitamente: `segunda planilla 24-08-2026`.
    """

    def __init__(self, ordinal: int):
        self._ordinal = ordinal
        word = ORDINAL_WORDS.get(ordinal)
        self.name = f"{word} planilla" if word else f"{ordinal} planilla"
        aliases = [f"{ordinal} planilla", f"{ordinal}a planilla"]
        if word:
            aliases.append(f"{word} planilla")
        # El nombre canónico no debe repetirse como alias.
        self.aliases = tuple(dict.fromkeys(a for a in aliases if a != self.name))

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        date_str = self._resolve_date(ctx, args)
        if date_str is None:
            return f"⚠️ Formato de fecha inválido: '{args[0]}'. Usa dd-mm-aaaa."

        folder_id = ctx.business.sheets_folder_id
        sheet_name = sheet_name_for(date_str, self._ordinal)

        # 1. Si ya existe, solo se selecciona.
        existing_id = ctx.drive.find_sheet_by_name(folder_id, sheet_name)
        if existing_id:
            ctx.session.set_active_sheet(existing_id, sheet_name)
            return f"Planilla '{sheet_name}' seleccionada."

        # 2. Debe existir la planilla inmediatamente anterior del mismo día.
        previous_name = sheet_name_for(date_str, self._ordinal - 1)
        previous_id = ctx.drive.find_sheet_by_name(folder_id, previous_name)
        if previous_id is None:
            return (
                f"⚠️ No existe la planilla '{previous_name}'. "
                "Las planillas adicionales se crean en orden."
            )

        # 3. Crear duplicando la plantilla en la carpeta del mes.
        duplicated = ctx.drive.duplicate_template(folder_id, sheet_name)
        if duplicated is None:
            log_warning(
                f"comando '{self.name}' no pudo crear la planilla",
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"folder_id={folder_id} sheet_name={sheet_name!r} "
                f"-> ver log previo de DriveClient",
            )
            return f"⚠️ No se pudo crear la planilla: '{sheet_name}'."
        sheet_id, _ = duplicated

        # 4. Inicializar: B42 = saldo total (B58) de la planilla anterior del día.
        ok, warning = _initialize_new_sheet(ctx, sheet_id, date_str, previous_id)
        if not ok:
            log_warning(
                f"comando '{self.name}' creó la planilla pero no pudo inicializarla",
                f"business_id={ctx.business.id} sheet_id={sheet_id} "
                f"sheet_name={sheet_name!r} previous_id={previous_id} "
                f"-> ver log previo de SheetsClient",
            )
            return f"⚠️ La planilla '{sheet_name}' se creó pero no pudo inicializarse."

        ctx.session.set_active_sheet(sheet_id, sheet_name)
        message = (
            f"Planilla '{sheet_name}' seleccionada. "
            f"Saldo de caja cargado desde '{previous_name}'."
        )
        return f"{warning}\n\n{message}" if warning else message

    def _resolve_date(self, ctx: CommandContext, args: list[str]) -> str | None:
        """Fecha objetivo: argumento explícito, planilla activa, u hoy (zona del negocio)."""
        if args:
            candidate = args[0]
            return candidate if base_date_of(candidate) == candidate else None
        if ctx.session.active_sheet_name:
            base = base_date_of(ctx.session.active_sheet_name)
            if base:
                return base
        return today_str()


def build_additional_sheet_commands() -> list[AdditionalSheetCommand]:
    """Genera los comandos de planillas adicionales (2ª a N-ésima)."""
    return [
        AdditionalSheetCommand(ordinal)
        for ordinal in range(2, MAX_DAILY_SHEETS + 1)
    ]
