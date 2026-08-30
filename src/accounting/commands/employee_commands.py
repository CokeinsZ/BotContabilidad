"""Comandos de préstamos a trabajadores y vales del administrador."""
from accounting.commands.base import Command, CommandContext
from accounting.commands.region_entry import RegionEntryCommand
from accounting.session_manager import CommandResult, PendingSelection
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
        from accounting.session_manager import UndoSnapshot

        sheet_id = ctx.session.active_sheet_id
        region = ctx.sheets.layout.worker_loan_region

        if not ctx.sheets.append_to_region(sheet_id, region, [worker_name, amount]):
            return ["⚠️ No se pudo registrar el préstamo en la planilla."]

        ctx.session.undo_snapshot = UndoSnapshot(
            sheet_id=sheet_id,
            description=" ".join([self.name, *args]),
            region=region,
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
        sheet_date = base_date_of(ctx.session.active_sheet_name or "")
        if sheet_date is None:
            sheet_date = ""

        region = ctx.sheets.layout.worker_file_region
        if not ctx.sheets.append_to_region(file_id, region, [sheet_date, amount]):
            return [
                f"⚠️ No se pudo registrar el préstamo en el archivo de '{worker_name}'."
            ]
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
