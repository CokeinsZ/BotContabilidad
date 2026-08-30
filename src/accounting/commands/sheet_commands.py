"""Comandos para crear o seleccionar planillas diarias."""
from datetime import datetime, timedelta

from accounting.commands.base import Command, CommandContext
from accounting.sheet_naming import (
    MAX_DAILY_SHEETS,
    ORDINAL_WORDS,
    base_date_of,
    sheet_name_for,
)


def _initialize_new_sheet(
    ctx: CommandContext, sheet_id: str, date_str: str, previous_sheet_id: str | None
) -> bool:
    """Inicializa una planilla recién creada con UNA escritura por lotes.

    Escribe: nombre del business (A2), administrador (B6), fecha (B7) y, si
    hay planilla previa, su saldo total (B46) como saldo de caja (B42).
    """
    layout = ctx.sheets.layout
    updates = {
        layout.business_name_cell: [[ctx.business.name]],
        layout.admin_name_cell: [[ctx.administrator.name]],
        layout.date_cell: [[date_str]],
    }
    if previous_sheet_id:
        previous_balance = ctx.sheets.get_value(
            previous_sheet_id, layout.total_cash_cell
        )
        updates[layout.generated_cash_cell] = [
            [previous_balance if previous_balance is not None else 0]
        ]
    return ctx.sheets.set_values(sheet_id, updates)


class SelectSheetCommand(Command):
    """`hoja <dd-mm-aaaa>`: selecciona o crea la PRIMERA planilla del día.

    Al crearla, el saldo de caja (B42) se toma del saldo total (B46) de la
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
            current_date = datetime.strptime(sheet_name, "%d-%m-%Y")
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
            return f"⚠️ No se pudo crear o encontrar la planilla: '{sheet_name}'."
        sheet_id, _ = duplicated

        # 3. Saldo previo: planilla MÁS ALTA del día anterior.
        previous_day_name = (current_date - timedelta(days=1)).strftime("%d-%m-%Y")
        previous_day_sheets = ctx.drive.find_daily_sheets(folder_id, previous_day_name)
        previous_sheet_id = previous_day_sheets[-1][0] if previous_day_sheets else None

        # 4. Inicializar la planilla nueva con una sola escritura por lotes.
        if not _initialize_new_sheet(ctx, sheet_id, sheet_name, previous_sheet_id):
            return f"⚠️ La planilla '{sheet_name}' se creó pero no pudo inicializarse."

        ctx.session.set_active_sheet(sheet_id, sheet_name)

        message = f"Planilla '{sheet_name}' seleccionada."
        if previous_sheet_id is None:
            warning = (
                f"No existe una planilla para el día anterior: '{previous_day_name}',"
                "\npor lo tanto no se pudo cargar el balance anterior."
            )
            return f"{warning}\n\n{message}"
        return message


class AdditionalSheetCommand(Command):
    """`segunda planilla` / `2 planilla` / ...: planillas adicionales del día.

    La planilla N de un día toma como saldo de caja (B42) el saldo total
    (B46) de la planilla N-1 de ese mismo día. La fecha se toma de la
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
            if args:
                return f"⚠️ Formato de fecha inválido: '{args[0]}'. Usa dd-mm-aaaa."
            return (
                "⚠️ No hay una planilla activa para saber la fecha. "
                f"Indícala: '{self.name} dd-mm-aaaa'."
            )

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
            return f"⚠️ No se pudo crear la planilla: '{sheet_name}'."
        sheet_id, _ = duplicated

        # 4. Inicializar: B42 = saldo total (B46) de la planilla anterior del día.
        if not _initialize_new_sheet(ctx, sheet_id, date_str, previous_id):
            return f"⚠️ La planilla '{sheet_name}' se creó pero no pudo inicializarse."

        ctx.session.set_active_sheet(sheet_id, sheet_name)
        return (
            f"Planilla '{sheet_name}' seleccionada. "
            f"Saldo de caja cargado desde '{previous_name}'."
        )

    def _resolve_date(self, ctx: CommandContext, args: list[str]) -> str | None:
        """Fecha objetivo: argumento explícito, planilla activa, u hoy."""
        if args:
            candidate = args[0]
            return candidate if base_date_of(candidate) == candidate else None
        if ctx.session.active_sheet_name:
            base = base_date_of(ctx.session.active_sheet_name)
            if base:
                return base
        return datetime.now().strftime("%d-%m-%Y")


def build_additional_sheet_commands() -> list[AdditionalSheetCommand]:
    """Genera los comandos de planillas adicionales (2ª a N-ésima)."""
    return [
        AdditionalSheetCommand(ordinal)
        for ordinal in range(2, MAX_DAILY_SHEETS + 1)
    ]
