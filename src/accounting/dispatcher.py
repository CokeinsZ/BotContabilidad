"""Dispatcher de comandos: enruta texto de usuario al comando correspondiente."""
from typing import Iterable

from accounting.commands.base import Command, CommandContext
from accounting.session_manager import CommandResult


class CommandDispatcher:
    """Registro y resolución de comandos por nombre o alias (OCP).

    Agregar un comando nuevo no requiere modificar esta clase: basta con
    incluirlo en la lista de comandos inyectada. Soporta comandos de dos
    palabras (ej: "segunda planilla").
    """

    def __init__(self, commands: Iterable[Command]):
        self._handlers: dict[str, Command] = {}
        for command in commands:
            self.register(command)

    def register(self, command: Command) -> None:
        self._handlers[command.name] = command
        for alias in command.aliases:
            self._handlers[alias] = command

    def dispatch(self, ctx: CommandContext, full_command: str) -> list[str]:
        """Ejecuta el comando y devuelve la lista de mensajes de respuesta."""
        parts = full_command.split()
        if not parts:
            return ["⚠️ Comando vacío."]

        command, args = self._resolve(parts)
        if command is None:
            return [f"⚠️ Comando desconocido: {parts[0].lower()}"]

        print(f"Ejecutando comando: {command.name} con argumentos: {args}")
        return self._normalize(command.execute(ctx, args))

    def _resolve(self, parts: list[str]) -> tuple[Command | None, list[str]]:
        """Busca primero comandos de dos palabras, luego de una."""
        if len(parts) >= 2:
            two_words = f"{parts[0]} {parts[1]}".lower()
            command = self._handlers.get(two_words)
            if command is not None:
                return command, parts[2:]
        return self._handlers.get(parts[0].lower()), parts[1:]

    @staticmethod
    def _normalize(result: CommandResult) -> list[str]:
        return [result] if isinstance(result, str) else result
