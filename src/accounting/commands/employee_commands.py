"""Comandos de préstamos a trabajadores, nómina y vales del administrador."""
from accounting.commands.base import Command, CommandContext
from accounting.commands.region_entry import RegionEntryCommand
from accounting.money import cell_number, format_amount
from accounting.names import clean_worker_name, name_matches
from accounting.session_manager import CommandResult, PendingSelection
from accounting.sheet_naming import base_date_of
from accounting.undo import RegionEntryStep, WorkerPeriodStep
from config.clock import today_str
from config.log import log_error, log_warning
from sheets.sheets_client import FORMULA, RegionFullError

_NO_WORKERS_FOLDER = (
    "⚠️ Este negocio no tiene configurada la carpeta de trabajadores "
    "(workers_folder_id)"
)


# ----------------------------------------------------------------------
# Archivos de trabajadores (compartido por préstamo y nómina)
# ----------------------------------------------------------------------
def find_worker_files(ctx: CommandContext, folder_id: str, worker_name: str) -> list[tuple[str, str]]:
    """Archivos cuyo nombre contiene el buscado, sin importar mayúsculas ni tildes."""
    return [
        (file_id, name)
        for file_id, name in ctx.drive.list_files_in_folder(folder_id)
        if name_matches(worker_name, name)
    ]


def create_worker_file(ctx: CommandContext, folder_id: str, worker_name: str) -> str | None:
    """Duplica la plantilla para un trabajador nuevo y escribe el nombre del negocio."""
    created = ctx.drive.duplicate_workers_template(folder_id, worker_name)
    if created is None:
        return None
    file_id, _ = created
    ctx.sheets.set_values(
        file_id, {ctx.sheets.layout.worker_business_name_cell: [[ctx.business.name]]}
    )
    return file_id


def menu_prompt(worker_name: str) -> str:
    return f"Hay varios trabajadores con nombre similar a '{worker_name}'"


def menu_labels(worker_name: str, candidates: list[tuple[str, str]], create_option: bool) -> list[str]:
    """Etiqueta de cada opción del menú, en el orden de sus números (1..n)."""
    labels = [name for _file_id, name in candidates]
    if create_option:
        labels.append(f"Crear nuevo trabajador '{worker_name}'")
    return labels


def build_menu(worker_name: str, candidates: list[tuple[str, str]], footer: str,
               create_option: bool) -> str:
    lines = [f"⚠️ {menu_prompt(worker_name)}:\n"]
    for index, (_file_id, name) in enumerate(candidates, start=1):
        lines.append(f"{index}. {name}")
    if create_option:
        lines.append(f"{len(candidates) + 1}. ➕ Crear nuevo trabajador '{worker_name}'")
    lines.append(f"\n{footer}")
    return "\n".join(lines)


def ask_selection(ctx: CommandContext, worker_name: str, menu: str, options: int,
                  description: str, resolver, labels: list[str] | None = None) -> str:
    """Encola una pregunta numerada y devuelve lo que hay que mostrar ahora.

    Si un mensaje trae varios comandos ambiguos, se pregunta uno a la vez:
    el siguiente menú aparece al responder el anterior. La pregunta guarda lo
    que ya escribió el comando (ej: la fila en la planilla) para revertirlo
    si el usuario no elige ninguna opción.
    """
    steps, descriptions = ctx.undo.current_command()
    shown_now = ctx.session.ask(PendingSelection(
        description=", ".join(descriptions) or description,
        menu=menu, options=options, resolver=resolver,
        cancel_steps=steps, cancel_descriptions=descriptions,
        prompt=menu_prompt(worker_name),
        option_labels=list(labels or []),
        sheet_id=ctx.session.active_sheet_id,
        sheet_name=ctx.session.active_sheet_name,
    ))
    if shown_now:
        return menu
    return (
        f"⏳ También hay varios trabajadores con nombre similar a '{worker_name}': "
        "te preguntaré cuando respondas el menú anterior."
    )


def unique_sheet_title(base: str, existing: set[str]) -> str:
    """'24-11-2026' o, si ya existe, '24-11-2026 (2)', '24-11-2026 (3)', ..."""
    if base not in existing:
        return base
    index = 2
    while f"{base} ({index})" in existing:
        index += 1
    return f"{base} ({index})"


def _first_cell(values: dict, cell: str):
    rows = values.get(cell, [])
    return rows[0][0] if rows and rows[0] else None


# ----------------------------------------------------------------------
# Préstamos
# ----------------------------------------------------------------------
class WorkerLoanCommand(Command):
    """`trabajador <monto> <nombre>` (o `vale`): registra un PRÉSTAMO (vale) a un trabajador.

    El préstamo se registra primero en la planilla diaria (región de
    trabajadores). Solo si eso funciona se registra ADEMÁS en el archivo
    individual del trabajador dentro de la carpeta `workers_folder_id`:

    - Si no existe archivo para ese nombre, se crea duplicando la plantilla.
    - Si existe exactamente uno, se usa.
    - Si hay varios con nombre similar, se le pide al usuario que elija
      respondiendo con un número (o que cree uno nuevo con la última opción).
    """

    name = "trabajador"
    aliases = ("trabajadores", "t", "vale", "vales", "v")

    def execute(self, ctx: CommandContext, args: list[str]) -> CommandResult:
        if error := self.require_active_sheet(ctx):
            return error
        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y el nombre del trabajador."

        try:
            amount = cell_number(self.parse_amount(args[0]))
        except ValueError as error:
            log_error(
                "comando 'trabajador' con monto inválido",
                error,
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} args={args}",
            )
            return "⚠️ El monto del préstamo debe ser un número válido."
        worker_name = clean_worker_name(" ".join(args[1:]))

        # 1. Planilla diaria (es el movimiento de caja). Si falla, NO se
        #    toca el archivo del trabajador: quedarían descuadrados.
        ok, message = self._record_in_daily_sheet(ctx, amount, worker_name, args)
        if not ok:
            return message

        # 2. Archivo individual del trabajador.
        sheet_date = base_date_of(ctx.session.active_sheet_name or "") or ""
        return [message, *self._record_in_worker_file(ctx, amount, worker_name, sheet_date)]

    # ------------------------------------------------------------------
    # Planilla diaria
    # ------------------------------------------------------------------
    def _record_in_daily_sheet(
        self, ctx: CommandContext, amount, worker_name: str, args: list[str]
    ) -> tuple[bool, str]:
        sheet_id = ctx.session.active_sheet_id
        region = ctx.sheets.layout.worker_loan_region
        values = [worker_name, amount]

        try:
            row = ctx.sheets.append_to_region(sheet_id, region, values)
        except RegionFullError:
            return False, self.region_full_message(region)
        except Exception as error:
            log_error(
                "comando 'trabajador' falló en planilla diaria (excepción)",
                error,
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"sheet_id={sheet_id} worker={worker_name!r} amount={amount} args={args}",
            )
            return False, "⚠️ No se pudo registrar el préstamo en la planilla."
        if row is None:
            log_warning(
                "comando 'trabajador' no pudo registrar en planilla diaria",
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} "
                f"sheet_id={sheet_id} sheet_name={ctx.session.active_sheet_name!r} "
                f"worker={worker_name!r} amount={amount} -> ver log previo de SheetsClient",
            )
            return False, "⚠️ No se pudo registrar el préstamo en la planilla."

        ctx.undo.record(
            [RegionEntryStep(sheet_id=sheet_id, region=region, row=row, values=values)],
            description=" ".join([self.name, *args]),
        )
        return True, f"Préstamo registrado: {format_amount(amount)} - {worker_name}"

    # ------------------------------------------------------------------
    # Archivo individual del trabajador
    # ------------------------------------------------------------------
    def _record_in_worker_file(
        self, ctx: CommandContext, amount, worker_name: str, sheet_date: str
    ) -> list[str]:
        folder_id = ctx.business.workers_folder_id
        if not folder_id:
            return [f"{_NO_WORKERS_FOLDER}, así que el préstamo no se registró en el archivo individual."]

        candidates = find_worker_files(ctx, folder_id, worker_name)

        if len(candidates) > 1:
            return [ask_selection(
                ctx, worker_name, self._menu(worker_name, candidates),
                options=len(candidates) + 1,
                description=f"trabajador {amount} {worker_name}",
                resolver=self._make_selection_resolver(amount, worker_name, sheet_date, candidates),
                labels=menu_labels(worker_name, candidates, create_option=True),
            )]

        if len(candidates) == 1:
            file_id, file_name = candidates[0]
            return self._record_loan(ctx, file_id, amount, file_name, sheet_date)

        return self._create_and_record(ctx, folder_id, amount, worker_name, sheet_date)

    def _create_and_record(
        self, ctx: CommandContext, folder_id: str, amount, worker_name: str, sheet_date: str
    ) -> list[str]:
        file_id = create_worker_file(ctx, folder_id, worker_name)
        if file_id is None:
            log_warning(
                "comando 'trabajador' no pudo crear archivo de trabajador",
                f"business_id={ctx.business.id} folder_id={folder_id} "
                f"worker={worker_name!r} amount={amount} -> ver log previo de DriveClient",
            )
            return [f"⚠️ No se pudo crear el archivo del trabajador '{worker_name}'."]
        return [
            f"👤 Se creó el archivo del trabajador '{worker_name}'.",
            *self._record_loan(ctx, file_id, amount, worker_name, sheet_date),
        ]

    def _record_loan(
        self, ctx: CommandContext, file_id: str, amount, worker_name: str, sheet_date: str
    ) -> list[str]:
        """Escribe [fecha, monto] en la fila indicada por el contador C123.

        `worker_name` es el nombre del ARCHIVO (para que el mensaje diga en
        cuál quedó, ej. 'maria fernanda' aunque el usuario escribió 'maria').
        """
        region = ctx.sheets.layout.worker_file_region
        values = [sheet_date, amount]
        try:
            row = ctx.sheets.append_to_region(file_id, region, values)
        except RegionFullError:
            return [
                f"⚠️ El archivo de '{worker_name}' ya tiene sus {region.capacity} vales "
                "ocupados: haz la nómina para cerrar el período. El préstamo quedó "
                "registrado solo en la planilla."
            ]
        except Exception as error:
            log_error(
                "comando 'trabajador' falló en archivo individual (excepción)",
                error,
                f"business_id={ctx.business.id} file_id={file_id} "
                f"worker={worker_name!r} amount={amount} date={sheet_date!r}",
            )
            row = None
        if row is None:
            log_warning(
                "comando 'trabajador' no pudo escribir en archivo individual",
                f"business_id={ctx.business.id} file_id={file_id} worker={worker_name!r} "
                f"amount={amount} date={sheet_date!r} -> ver log previo de SheetsClient",
            )
            return [f"⚠️ No se pudo registrar el préstamo en el archivo de '{worker_name}'."]

        ctx.undo.record([RegionEntryStep(sheet_id=file_id, region=region, row=row, values=values)])
        return [f"📄 Préstamo guardado en el archivo de '{worker_name}'."]

    # ------------------------------------------------------------------
    # Selección cuando hay varios trabajadores similares
    # ------------------------------------------------------------------
    @staticmethod
    def _menu(worker_name: str, candidates: list[tuple[str, str]]) -> str:
        return build_menu(worker_name, candidates, "Responde con el número de la opción.",
                          create_option=True)

    def _make_selection_resolver(
        self, amount, worker_name: str, sheet_date: str, candidates: list[tuple[str, str]]
    ):
        """Crea la closure que resuelve la selección numérica del usuario."""

        def resolve(ctx: CommandContext, option: int) -> CommandResult:
            if option <= len(candidates):
                file_id, file_name = candidates[option - 1]
                return self._record_loan(ctx, file_id, amount, file_name, sheet_date)
            # Última opción: crear un trabajador nuevo con el nombre escrito.
            return self._create_and_record(
                ctx, ctx.business.workers_folder_id, amount, worker_name, sheet_date
            )

        return resolve


class AdminPaymentCommand(RegionEntryCommand):
    """`administrador <monto>`: vales para el administrador/dueño."""

    name = "administrador"
    aliases = ("admin",)
    region_attr = "admin_region"
    success_label = "Pago administrativo registrado"
    missing_args_message = "⚠️ Debes proporcionar el monto del pago."
    invalid_amount_message = "⚠️ El monto del pago debe ser un número válido."

    def validate_args(self, args: list[str]) -> str | None:
        return self.missing_args_message if len(args) < 1 else None

    def build_row(self, args: list[str]) -> list:
        return [cell_number(self.parse_amount(args[0]))]


# ----------------------------------------------------------------------
# Nómina
# ----------------------------------------------------------------------
class NominaCommand(Command):
    """`nomina <monto> <nombre>`: paga y cierra el período de un trabajador.

    1. Registra el monto en la planilla diaria (región de trabajadores).
    2. Cierra el período del trabajador en su archivo (`close_worker_period`):
       - Mensaje con: nombre, suma de préstamos (B30) y URL al archivo.
       - Duplica la hoja "principal", borra las filas 1-9 de la copia y la
         nombra con la fecha de hoy (dd-mm-aaaa; si ya existe, "(2)", ...).
       - Limpia los vales de la hoja principal (A13:C28, B en 0) y reinicia
         el contador C123 a 13.

    Todo es deshacible: deshacer borra la hoja archivada y restaura los
    vales. El cierre también lo reutiliza `retiro` cuando la descripción es
    `nomina <nombre>`.
    """

    name = "nomina"
    aliases = ("nómina", "n")

    def execute(self, ctx: CommandContext, args: list[str]) -> CommandResult:
        if error := self.require_active_sheet(ctx):
            return error
        if len(args) < 2:
            return "⚠️ Formato: nomina <monto> <nombre>."

        try:
            amount = cell_number(self.parse_amount(args[0]))
        except ValueError as error:
            log_error(
                "comando 'nomina' con monto inválido",
                error,
                f"business_id={ctx.business.id} phone={ctx.session.phone_number} args={args}",
            )
            return "⚠️ El monto debe ser un número válido."
        worker_name = clean_worker_name(" ".join(args[1:]))

        # 1. Registrar el pago en la planilla diaria (región de trabajadores).
        sheet_id = ctx.session.active_sheet_id
        region = ctx.sheets.layout.worker_loan_region
        values = [worker_name, amount]
        try:
            row = ctx.sheets.append_to_region(sheet_id, region, values)
        except RegionFullError:
            return self.region_full_message(region)
        except Exception as error:
            log_error(
                "comando 'nomina' falló en planilla diaria (excepción)",
                error,
                f"business_id={ctx.business.id} sheet_id={sheet_id} "
                f"worker={worker_name!r} amount={amount} args={args}",
            )
            row = None
        if row is None:
            log_warning(
                "comando 'nomina' no pudo registrar en planilla diaria",
                f"business_id={ctx.business.id} sheet_id={sheet_id} "
                f"sheet_name={ctx.session.active_sheet_name!r} worker={worker_name!r} "
                f"amount={amount} -> ver log previo de SheetsClient",
            )
            return "⚠️ No se pudo registrar el pago en la planilla diaria."

        ctx.undo.record(
            [RegionEntryStep(sheet_id=sheet_id, region=region, row=row, values=values)],
            description=" ".join([self.name, *args]),
        )
        messages = [f"Pago de nómina registrado en planilla: {format_amount(amount)} - {worker_name}"]

        # 2. Cerrar el período del trabajador en su archivo.
        messages.extend(self.close_worker_period(ctx, worker_name))
        return messages

    # ------------------------------------------------------------------
    # Cierre del período (reutilizable por otros comandos, ej: retiro)
    # ------------------------------------------------------------------
    def close_worker_period(self, ctx: CommandContext, worker_name: str) -> list[str]:
        """Busca el archivo del trabajador y cierra su período.

        Maneja la desambiguación (menú numerado) cuando hay varios archivos
        con nombre similar.
        """
        folder_id = ctx.business.workers_folder_id
        if not folder_id:
            return [f"{_NO_WORKERS_FOLDER}."]

        candidates = find_worker_files(ctx, folder_id, worker_name)
        if not candidates:
            return [f"⚠️ No se encontró archivo para el trabajador '{worker_name}'."]

        if len(candidates) > 1:
            return [ask_selection(
                ctx, worker_name, self._menu(worker_name, candidates),
                options=len(candidates),
                description=f"nomina {worker_name}",
                resolver=self._make_selection_resolver(candidates),
                labels=menu_labels(worker_name, candidates, create_option=False),
            )]

        file_id, file_name = candidates[0]
        return self._process_nomina(ctx, file_id, file_name)

    def _process_nomina(self, ctx: CommandContext, file_id: str, worker_name: str) -> list[str]:
        """Archiva la hoja principal y la deja lista para el siguiente período."""
        layout = ctx.sheets.layout
        region = layout.worker_file_region
        block_range = region.block_range(region.min_row, region.max_row)
        context = f"business_id={ctx.business.id} file_id={file_id} worker={worker_name!r}"

        with ctx.sheets.lock(file_id):
            sheets_list = ctx.sheets.list_sheets(file_id)
            if sheets_list is None:
                return [f"⚠️ No se pudo leer el archivo de '{worker_name}'."]
            main_sheet_id = next(
                (sid for sid, title in sheets_list if title.lower() == layout.worker_main_sheet),
                None,
            )
            if main_sheet_id is None:  # ojo: el sheetId 0 es válido
                log_warning("nómina: el archivo no tiene hoja principal", f"{context} sheets={sheets_list}")
                return [f"⚠️ El archivo de '{worker_name}' no tiene la hoja '{layout.worker_main_sheet}'."]

            values = ctx.sheets.get_values(file_id, [layout.worker_loan_sum_cell, region.counter_cell])
            block = ctx.sheets.get_values(file_id, [block_range], FORMULA)
            if values is None or block is None:
                return [f"⚠️ No se pudo leer el archivo de '{worker_name}'."]
            loan_sum = _first_cell(values, layout.worker_loan_sum_cell) or 0
            previous_counter = _first_cell(values, region.counter_cell)
            previous_block = [
                list(row) + [""] * (region.width - len(row)) for row in block.get(block_range, [])
            ]
            previous_block += [[""] * region.width for _ in range(region.capacity - len(previous_block))]

            archive_name = unique_sheet_title(today_str(), {title for _, title in sheets_list})
            archived_sheet_id = ctx.sheets.duplicate_sheet(file_id, main_sheet_id, archive_name)
            if archived_sheet_id is None:
                log_warning("nómina no pudo duplicar hoja principal", f"{context} archive={archive_name!r}")
                return [f"⚠️ No se pudo crear la hoja de nómina para '{worker_name}'."]

            first_row, last_row = layout.worker_archive_deleted_rows
            cleared = ctx.sheets.delete_rows(
                file_id, archived_sheet_id, first_row, last_row
            ) and ctx.sheets.set_values(
                file_id,
                {
                    block_range: [region.blank_row for _ in range(region.capacity)],
                    region.counter_cell: [[region.min_row]],
                },
            )
            if not cleared:
                # Revertir lo hecho para no dejar el archivo a medias.
                ctx.sheets.delete_sheet(file_id, archived_sheet_id)
                log_warning("nómina no pudo limpiar la hoja principal", f"{context} archive={archive_name!r}")
                return [f"⚠️ No se pudo cerrar el período de '{worker_name}'."]

        ctx.undo.record([
            WorkerPeriodStep(
                file_id=file_id,
                worker_name=worker_name,
                archived_sheet_id=archived_sheet_id,
                region=region,
                previous_block=previous_block,
                previous_counter=previous_counter if previous_counter is not None else region.min_row,
                reset_counter=region.min_row,
            )
        ])
        sheet_url = f"https://docs.google.com/spreadsheets/d/{file_id}/edit?usp=sharing"
        return [
            f"📋 Nómina de {worker_name}\n"
            f"Suma de préstamos: {format_amount(loan_sum)}\n"
            f"Archivo: {sheet_url}",
            f"✅ Nómina procesada: hoja '{archive_name}' creada y hoja principal limpiada.",
        ]

    @staticmethod
    def _menu(worker_name: str, candidates: list[tuple[str, str]]) -> str:
        return build_menu(
            worker_name, candidates,
            "Responde con el número del trabajador para hacer nómina.",
            create_option=False,
        )

    def _make_selection_resolver(self, candidates: list[tuple[str, str]]):
        def resolve(ctx: CommandContext, option: int) -> CommandResult:
            file_id, file_name = candidates[option - 1]
            return self._process_nomina(ctx, file_id, file_name)

        return resolve
