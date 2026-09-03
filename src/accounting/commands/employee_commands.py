"""Comandos de préstamos a trabajadores y vales del administrador."""
from datetime import datetime
from accounting.commands.base import Command, CommandContext
from accounting.commands.region_entry import RegionEntryCommand
from accounting.session_manager import CommandResult, PendingSelection, UndoSnapshot
from accounting.sheet_naming import base_date_of


class WorkerLoanCommand(Command):
    """`trabajador <monto> <nombre>`: registra un PRÉSTAMO a un trabajador.

    (Históricamente llamado "pago": lo que se registra es dinero que sale de
    caja como préstamo y se descuenta después, no un pago de nómina.)

    El préstamo se registra SIEMPRE en la planilla diaria (región de
    trabajadores) y ADEMÁS en el archivo individual del trabajador dentro de
    la carpeta `workers_folder_id` del business (Formato_Trabajadores):

    - Si no existe archivo para ese nombre, se crea duplicando la plantilla.
    - Si existe exactamente uno, se usa.
    - Si hay varios con nombre similar, se le pide al usuario que elija
      respondiendo con un número (o que cree uno nuevo con la última opción).
    """

    name = "trabajador"
    aliases = ("trabajadores", "t")

    def execute(self, ctx: CommandContext, args: list[str]) -> CommandResult:
        if error := self.require_active_sheet(ctx):
            return error
        if len(args) < 2:
            return "⚠️ Debes proporcionar el monto y el nombre del trabajador."

        try:
            amount = self.parse_amount(args[0])
        except ValueError:
            return "⚠️ El monto del préstamo debe ser un número válido."
        worker_name = " ".join(args[1:])

        # 1. Registrar en la planilla diaria (siempre: es el movimiento de caja).
        messages = self._record_in_daily_sheet(ctx, amount, worker_name, args)

        # 2. Registrar en el archivo individual del trabajador (si aplica).
        messages.extend(self._record_in_worker_file(ctx, amount, worker_name))
        return messages

    # ------------------------------------------------------------------
    # Planilla diaria
    # ------------------------------------------------------------------
    def _record_in_daily_sheet(
        self, ctx: CommandContext, amount: float, worker_name: str, args: list[str]
    ) -> list[str]:
        from accounting.session_manager import UndoSnapshot, UndoStep

        sheet_id = ctx.session.active_sheet_id
        region = ctx.sheets.layout.worker_loan_region

        if not ctx.sheets.append_to_region(sheet_id, region, [worker_name, amount]):
            return ["⚠️ No se pudo registrar el préstamo en la planilla."]

        # Guardar info para el undo del archivo del trabajador (se completa después)
        ctx.session.undo_snapshot = UndoSnapshot(
            description=" ".join([self.name, *args]),
            steps=[
                UndoStep(sheet_id=sheet_id, region=region),
            ],
        )
        return [f"Préstamo registrado: {amount} - {worker_name}"]

    # ------------------------------------------------------------------
    # Archivo individual del trabajador
    # ------------------------------------------------------------------
    def _record_in_worker_file(
        self, ctx: CommandContext, amount: float, worker_name: str
    ) -> list[str]:
        folder_id = ctx.business.workers_folder_id
        if not folder_id:
            return [
                "⚠️ Este negocio no tiene configurada la carpeta de trabajadores "
                "(workers_folder_id), así que el préstamo no se registró en el "
                "archivo individual."
            ]

        candidates = self._find_worker_files(ctx, folder_id, worker_name)

        if len(candidates) > 1:
            return [self._ask_for_selection(ctx, amount, worker_name, candidates)]

        if len(candidates) == 1:
            file_id, file_name = candidates[0]
            return self._record_loan(ctx, file_id, amount, worker_name)

        # Sin archivos similares: crear uno nuevo y registrar.
        created = ctx.drive.duplicate_workers_template(folder_id, worker_name)
        if created is None:
            return [f"⚠️ No se pudo crear el archivo del trabajador '{worker_name}'."]
        file_id, _ = created

        messages = [f"👤 Se creó el archivo del trabajador '{worker_name}'."]
        messages.extend(self._record_loan(ctx, file_id, amount, worker_name))
        return messages

    def _record_loan(
        self, ctx: CommandContext, file_id: str, amount: float, worker_name: str
    ) -> list[str]:
        """Escribe [fecha, monto] en la fila indicada por el contador C123."""
        from accounting.session_manager import UndoStep

        sheet_date = base_date_of(ctx.session.active_sheet_name or "")
        if sheet_date is None:
            sheet_date = ""

        region = ctx.sheets.layout.worker_file_region
        if not ctx.sheets.append_to_region(file_id, region, [sheet_date, amount]):
            return [
                f"⚠️ No se pudo registrar el préstamo en el archivo de '{worker_name}'."
            ]

        # Agregar paso de undo para el archivo del trabajador
        if ctx.session.undo_snapshot is not None:
            ctx.session.undo_snapshot.steps.append(
                UndoStep(sheet_id=file_id, region=region)
            )
        else:
            # Caso borde: solo archivo, sin planilla (no debería pasar)
            ctx.session.undo_snapshot = UndoSnapshot.single(
                description=f"trabajador {amount} {worker_name} (solo archivo)",
                sheet_id=file_id,
                region=region,
            )

        return [f"📄 Préstamo guardado en el archivo de '{worker_name}'."]

    # ------------------------------------------------------------------
    # Selección cuando hay varios trabajadores similares
    # ------------------------------------------------------------------
    def _find_worker_files(
        self, ctx: CommandContext, folder_id: str, worker_name: str
    ) -> list[tuple[str, str]]:
        """Archivos de la carpeta cuyo nombre contiene el nombre buscado."""
        query = worker_name.lower()
        return [
            (file_id, name)
            for file_id, name in ctx.drive.list_files_in_folder(folder_id)
            if query in name.lower()
        ]

    def _ask_for_selection(
        self,
        ctx: CommandContext,
        amount: float,
        worker_name: str,
        candidates: list[tuple[str, str]],
    ) -> str:
        ctx.session.pending_selection = PendingSelection(
            description=f"trabajador {amount} {worker_name}",
            resolver=self._make_selection_resolver(amount, worker_name, candidates),
        )
        return self._build_menu(worker_name, candidates)

    def _make_selection_resolver(
        self, amount: float, worker_name: str, candidates: list[tuple[str, str]]
    ):
        """Crea la closure que resuelve la selección numérica del usuario."""

        def resolve(ctx: CommandContext, text: str) -> CommandResult:
            folder_id = ctx.business.workers_folder_id
            option = int(text)
            new_option = len(candidates) + 1

            if 1 <= option <= len(candidates):
                file_id, file_name = candidates[option - 1]
                return self._record_loan(ctx, file_id, amount, worker_name)

            if option == new_option:
                created = ctx.drive.duplicate_workers_template(folder_id, worker_name)
                if created is None:
                    return [
                        f"⚠️ No se pudo crear el archivo del trabajador '{worker_name}'."
                    ]
                file_id, _ = created
                messages = [f"👤 Se creó el archivo del trabajador '{worker_name}'."]
                messages.extend(self._record_loan(ctx, file_id, amount, worker_name))
                return messages

            # Opción inválida: mantener la selección pendiente y re-mostrar.
            ctx.session.pending_selection = PendingSelection(
                description=f"trabajador {amount} {worker_name}",
                resolver=self._make_selection_resolver(amount, worker_name, candidates),
            )
            return [
                f"⚠️ Opción inválida: {option}.",
                self._build_menu(worker_name, candidates),
            ]

        return resolve

    @staticmethod
    def _build_menu(worker_name: str, candidates: list[tuple[str, str]]) -> str:
        lines = [f"⚠️ Hay varios trabajadores con nombre similar a '{worker_name}':\n"]
        for index, (_file_id, name) in enumerate(candidates, start=1):
            lines.append(f"{index}. {name}")
        lines.append(f"{len(candidates) + 1}. ➕ Crear nuevo trabajador '{worker_name}'")
        lines.append("\nResponde con el número de la opción.")
        return "\n".join(lines)


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
        return [self.parse_amount(args[0])]


class NominaCommand(Command):
    """`nomina <monto> <nombre>`: paga y cierra el período de un trabajador.

    1. Registra el monto en la planilla diaria (región de trabajadores).
    2. Cierra el período del trabajador en su archivo (`close_worker_period`):
       - Envía mensaje con: nombre, suma de préstamos (B30) y URL al archivo.
       - Duplica la hoja "principal", borra filas 1-9 y la nombra con la fecha
         de hoy (dd-mm-yyyy, fecha de ejecución).
       - Limpia la hoja principal: A13:A28 y C13:C28 vacíos, B13:B28 ceros,
         y reinicia el contador C123 a 13.

    El proceso de cierre también es reutilizado por `retiro` cuando la
    descripción es `nomina <nombre>`.
    """

    name = "nomina"
    aliases = ("nómina", "n")

    def execute(self, ctx: CommandContext, args: list[str]) -> CommandResult:
        if error := self.require_active_sheet(ctx):
            return error
        if len(args) < 2:
            return "⚠️ Formato: nomina <monto> <nombre>."

        try:
            amount = self.parse_amount(args[0])
        except ValueError:
            return "⚠️ El monto debe ser un número válido."
        worker_name = " ".join(args[1:])

        # 1. Registrar el pago en la planilla diaria (región de trabajadores).
        sheet_id = ctx.session.active_sheet_id
        region = ctx.sheets.layout.worker_loan_region
        if not ctx.sheets.append_to_region(sheet_id, region, [worker_name, amount]):
            return "⚠️ No se pudo registrar el pago en la planilla diaria."

        ctx.session.undo_snapshot = UndoSnapshot.single(
            description=" ".join([self.name, *args]),
            sheet_id=sheet_id,
            region=region,
        )

        messages = [f"Pago registrado en planilla: {amount} - {worker_name}"]

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
            return [
                "⚠️ Este negocio no tiene configurada la carpeta de trabajadores "
                "(workers_folder_id)."
            ]

        candidates = self._find_worker_files(ctx, folder_id, worker_name)
        if not candidates:
            return [f"⚠️ No se encontró archivo para el trabajador '{worker_name}'."]

        if len(candidates) > 1:
            return [self._ask_for_selection_nomina(ctx, worker_name, candidates)]

        file_id, file_name = candidates[0]
        return self._process_nomina(ctx, file_id, file_name, worker_name)

    def _find_worker_files(
        self, ctx: CommandContext, folder_id: str, worker_name: str
    ) -> list[tuple[str, str]]:
        """Archivos de la carpeta cuyo nombre contiene el nombre buscado."""
        query = worker_name.lower().replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ú", "u").strip()
        return [
            (file_id, name)
            for file_id, name in ctx.drive.list_files_in_folder(folder_id)
            if query in name.lower()
        ]

    def _process_nomina(
        self, ctx: CommandContext, file_id: str, file_name: str, worker_name: str
    ) -> CommandResult:
        """Ejecuta el cierre del período en el archivo del trabajador."""
        today = datetime.now().strftime("%d-%m-%Y")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{file_id}/edit?usp=sharing"

        messages = []

        # 1. Leer suma de préstamos (B30) y enviar mensaje
        loan_sum = ctx.sheets.get_worker_loan_sum(file_id) or "0"
        messages.append(
            f"📋 Nómina de {worker_name}\n"
            f"Suma de préstamos: {loan_sum}\n"
            f"Archivo: {sheet_url}"
        )

        # 2. Duplicar hoja principal, borrar filas 1-9, renombrar a fecha de hoy
        main_sheet_id = ""
        spreadsheet = ctx.sheets.service.spreadsheets().get(
            spreadsheetId=file_id, fields="sheets(properties(sheetId,title))"
        ).execute()
        sheets_props = spreadsheet.get("sheets", [])
        if not sheets_props:
            return [f"⚠️ No se encontraron hojas en el archivo de '{worker_name}'."]
        for sheet in sheets_props:
            if sheet["properties"]["title"].lower() == "principal":
                main_sheet_id = sheet["properties"]["sheetId"]
                break
        if not main_sheet_id:
            main_sheet_id = sheets_props[0]["properties"]["sheetId"]

        new_sheet_id = ctx.sheets.duplicate_sheet(file_id, main_sheet_id, today)
        if new_sheet_id is None:
            return [f"⚠️ No se pudo crear la hoja de nómina para '{worker_name}'."]

        # Borrar filas 1-9 (índices 0-8) en la nueva hoja
        if not ctx.sheets.delete_rows(file_id, new_sheet_id, 1, 10):
            return ["⚠️ No se pudieron borrar las filas 1-9 en la hoja de nómina."]

        # 3. Limpiar hoja principal: A13:A28 vacíos, B13:B28 ceros, C13:C28 vacíos, C123=13
        sheet_prefix = "principal!"  # Asumiendo que la hoja principal se llama "principal"

        # A13:A28 -> vacíos (strings vacíos)
        ctx.sheets.clear_range_a1(file_id, f"{sheet_prefix}A13:A28", "")
        # B13:B28 -> ceros
        ctx.sheets.clear_range_a1(file_id, f"{sheet_prefix}B13:B28", 0)
        # C13:C28 -> vacíos (strings vacíos)
        ctx.sheets.clear_range_a1(file_id, f"{sheet_prefix}C13:C28", "")
        # C123 = 13
        ctx.sheets.reset_counter(file_id, f"{sheet_prefix}C123", 13)

        messages.append(f"✅ Nómina procesada: hoja '{today}' creada y hoja principal limpiada.")
        return messages

    def _ask_for_selection_nomina(
        self, ctx: CommandContext, worker_name: str, candidates: list[tuple[str, str]]
    ) -> str:
        """Pide al usuario que elija cuál archivo usar para la nómina."""
        ctx.session.pending_selection = PendingSelection(
            description=f"nomina {worker_name}",
            resolver=self._make_selection_resolver_nomina(worker_name, candidates),
        )
        return self._build_menu_nomina(worker_name, candidates)

    def _make_selection_resolver_nomina(
        self, worker_name: str, candidates: list[tuple[str, str]]
    ):
        def resolve(ctx: CommandContext, text: str) -> CommandResult:
            option = int(text)
            if 1 <= option <= len(candidates):
                file_id, file_name = candidates[option - 1]
                return self._process_nomina(ctx, file_id, file_name, worker_name)
            # Opción inválida
            ctx.session.pending_selection = PendingSelection(
                description=f"nomina {worker_name}",
                resolver=self._make_selection_resolver_nomina(worker_name, candidates),
            )
            return [
                f"⚠️ Opción inválida: {option}.",
                self._build_menu_nomina(worker_name, candidates),
            ]
        return resolve

    @staticmethod
    def _build_menu_nomina(worker_name: str, candidates: list[tuple[str, str]]) -> str:
        lines = [f"⚠️ Hay varios trabajadores con nombre similar a '{worker_name}':\n"]
        for index, (_file_id, name) in enumerate(candidates, start=1):
            lines.append(f"{index}. {name}")
        lines.append("\nResponde con el número del trabajador para hacer nómina.")
        return "\n".join(lines)
