"""Dispatcher de comandos: enruta texto de usuario al comando correspondiente."""
from typing import Iterable

from accounting.commands.base import Command, CommandContext


class CommandDispatcher:
    """Registro y resolución de comandos por nombre o alias (OCP).

    Agregar un comando nuevo no requiere modificar esta clase: basta con
    incluirlo en la lista de comandos inyectada.
    """

    def __init__(self, commands: Iterable[Command]):
        self._handlers: dict[str, Command] = {}
        for command in commands:
            self.register(command)

    def register(self, command: Command) -> None:
        self._handlers[command.name] = command
        for alias in command.aliases:
            self._handlers[alias] = command

    def dispatch(self, ctx: CommandContext, full_command: str) -> str:
        parts = full_command.split()
        if not parts:
            return "⚠️ Comando vacío."

        cmd, args = parts[0].lower(), parts[1:]
        print(f"Ejecutando comando: {cmd} con argumentos: {args}")

        command = self._handlers.get(cmd)
        if command is None:
            return f"⚠️ Comando desconocido: {cmd}"
        return command.execute(ctx, args)
