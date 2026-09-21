"""Comandos del bot de contabilidad."""
from accounting.commands.base import Command, CommandContext
from accounting.commands.sheet_commands import (
    SelectSheetCommand,
    build_additional_sheet_commands,
)
from accounting.commands.expense_commands import (
    CleaningExpenseCommand,
    ExpenseCommand,
    FeedingExpenseCommand,
)
from accounting.commands.cash_commands import (
    BalanceCommand,
    CashCommand,
    InvestmentCommand,
    WithdrawalCommand,
)
from accounting.commands.employee_commands import (
    AdminPaymentCommand,
    NominaCommand,
    WorkerLoanCommand,
)
from accounting.commands.summary_command import SummaryCommand
from accounting.commands.undo_command import UndoCommand
from accounting.commands.help_command import HelpCommand


def build_default_commands() -> list[Command]:
    """Construye la lista de comandos disponibles del bot."""
    nomina_command = NominaCommand()
    return [
        SelectSheetCommand(),
        *build_additional_sheet_commands(),
        ExpenseCommand(),
        CleaningExpenseCommand(),
        FeedingExpenseCommand(),
        WorkerLoanCommand(),
        nomina_command,
        AdminPaymentCommand(),
        WithdrawalCommand(nomina_command),
        BalanceCommand(),
        CashCommand(),
        InvestmentCommand(),
        SummaryCommand(),
        UndoCommand(),
        HelpCommand(),
    ]


__all__ = [
    "Command",
    "CommandContext",
    "build_default_commands",
]
