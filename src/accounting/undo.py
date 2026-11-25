"""
Deshacer: pasos atómicos, snapshots por mensaje y grabación por lote.

Un mensaje de WhatsApp puede traer varios comandos (DeepSeek devuelve una
lista). Todos los pasos que esos comandos registran se agrupan en un solo
`UndoSnapshot`, de modo que `deshacer` revierte TODO lo que hizo el último
mensaje, en orden inverso.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from config.log import log_warning
from sheets.layout import SheetRegion
from sheets.sheets_client import RemoveResult, RestoreResult

if TYPE_CHECKING:
    from sheets.sheets_client import SheetsClient


class Outcome(Enum):
    DONE = "done"        # revertido
    SKIPPED = "skipped"  # no aplica / ya no existe / lo cambió otra persona
    FAILED = "failed"    # error de API: se puede reintentar


@dataclass(frozen=True)
class StepResult:
    outcome: Outcome
    note: str | None = None


class UndoStep(ABC):
    """Una operación atómica reversible."""

    @abstractmethod
    def undo(self, sheets: "SheetsClient") -> StepResult:
        ...


@dataclass
class RegionEntryStep(UndoStep):
    """Se agregó una fila a una región (gasto, préstamo, retiro, ...)."""

    sheet_id: str
    region: SheetRegion
    row: int
    values: list

    def undo(self, sheets: "SheetsClient") -> StepResult:
        result = sheets.remove_region_entry(self.sheet_id, self.region, self.row, self.values)
        if result is RemoveResult.REMOVED:
            return StepResult(Outcome.DONE)
        if result is RemoveResult.NOT_FOUND:
            return StepResult(
                Outcome.SKIPPED,
                f"el registro de '{self.region.label}' ya no estaba en la planilla",
            )
        return StepResult(Outcome.FAILED)


@dataclass
class CellStep(UndoStep):
    """Se sobrescribió una celda fija (saldo, efectivo)."""

    sheet_id: str
    cell: str
    written_value: object
    restore_value: object

    def undo(self, sheets: "SheetsClient") -> StepResult:
        result = sheets.restore_cell(self.sheet_id, self.cell, self.written_value, self.restore_value)
        if result is RestoreResult.RESTORED:
            return StepResult(Outcome.DONE)
        if result is RestoreResult.CHANGED:
            return StepResult(
                Outcome.SKIPPED,
                f"la celda {self.cell} fue modificada después, se dejó con su valor actual",
            )
        return StepResult(Outcome.FAILED)


@dataclass
class WorkerPeriodStep(UndoStep):
    """Se cerró el período de nómina de un trabajador.

    Revertir = borrar la hoja archivada y restaurar los vales y el contador
    de la hoja principal tal como estaban antes del cierre.
    """

    file_id: str
    worker_name: str
    archived_sheet_id: int
    region: SheetRegion
    previous_block: list[list]
    previous_counter: object
    reset_counter: int

    def undo(self, sheets: "SheetsClient") -> StepResult:
        region = self.region
        with sheets.lock(self.file_id):
            # Si después de la nómina se registraron vales nuevos, restaurar
            # el bloque los borraría: no se toca y se avisa.
            values = sheets.get_values(self.file_id, [region.counter_cell])
            if values is None:
                return StepResult(Outcome.FAILED)
            rows = values.get(region.counter_cell, [])
            counter = rows[0][0] if rows and rows[0] else None
            try:
                current_counter = int(counter)
            except (TypeError, ValueError):
                current_counter = None
            if current_counter != self.reset_counter:
                log_warning(
                    "deshacer nómina: el archivo recibió vales nuevos",
                    f"file_id={self.file_id} counter={counter!r} reset={self.reset_counter}",
                )
                return StepResult(
                    Outcome.SKIPPED,
                    f"el archivo de '{self.worker_name}' recibió vales nuevos después de la "
                    "nómina; restáuralo a mano desde la hoja archivada",
                )

            restored = sheets.write_preserving_formulas(
                self.file_id,
                {
                    region.block_range(region.min_row, region.max_row): self.previous_block,
                    region.counter_cell: [[self.previous_counter]],
                },
            )
            if not restored:
                return StepResult(Outcome.FAILED)
            if not sheets.delete_sheet(self.file_id, self.archived_sheet_id):
                return StepResult(
                    Outcome.SKIPPED,
                    f"se restauraron los vales de '{self.worker_name}' pero no se pudo "
                    "borrar la hoja archivada",
                )
            return StepResult(Outcome.DONE)


@dataclass
class UndoSnapshot:
    """Lo necesario para revertir el último mensaje del usuario."""

    descriptions: list[str]
    steps: list[UndoStep] = field(default_factory=list)

    @property
    def description(self) -> str:
        return ", ".join(self.descriptions)

    def without(self, steps: list[UndoStep], descriptions: list[str]) -> "UndoSnapshot | None":
        """Copia sin esos pasos/descripciones (None si queda vacío)."""
        remaining = [s for s in self.steps if not any(s is removed for removed in steps)]
        texts = list(self.descriptions)
        for text in descriptions:
            if text in texts:
                texts.remove(text)
        return UndoSnapshot(texts, remaining) if remaining else None


class UndoRecorder:
    """Acumula los pasos de deshacer de todos los comandos de un mensaje."""

    def __init__(self):
        self.descriptions: list[str] = []
        self.steps: list[UndoStep] = []
        self._command_start = (0, 0)

    def begin_command(self) -> None:
        """Marca el inicio de un comando (para saber qué pasos son suyos)."""
        self._command_start = (len(self.steps), len(self.descriptions))

    def current_command(self) -> tuple[list[UndoStep], list[str]]:
        """Pasos y descripciones registrados por el comando en curso."""
        steps_from, descriptions_from = self._command_start
        return list(self.steps[steps_from:]), list(self.descriptions[descriptions_from:])

    def record(self, steps: list[UndoStep], description: str | None = None) -> None:
        if description:
            self.descriptions.append(description)
        self.steps.extend(steps)

    def clear(self) -> None:
        self.descriptions.clear()
        self.steps.clear()
        self._command_start = (0, 0)

    @property
    def has_steps(self) -> bool:
        return bool(self.steps)

    def to_snapshot(self) -> UndoSnapshot:
        return UndoSnapshot(descriptions=list(self.descriptions), steps=list(self.steps))

    def merge_into(self, snapshot: UndoSnapshot | None) -> UndoSnapshot:
        """Agrega estos pasos a un snapshot existente (respuesta a un menú)."""
        if snapshot is None:
            return self.to_snapshot()
        return UndoSnapshot(
            descriptions=[*snapshot.descriptions, *self.descriptions],
            steps=[*snapshot.steps, *self.steps],
        )
