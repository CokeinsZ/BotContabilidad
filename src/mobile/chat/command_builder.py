"""Convierte lo que el administrador escribió en la app en comandos del bot.

1. Comando sin argumentos (deshacer, terminar_dia, corregir_saldos) -> directo.
2. Comando con argumentos y texto bien escrito -> directo, SIN DeepSeek:
   más rápido, determinista y sin costo. Acepta el monto al inicio o al
   final: "5.000 pan" o "pan 5.000" -> "gasto 5000 pan".
3. Lo demás ("5 mil de pan", "dos lucas") -> DeepSeek con "<comando> <texto>".
4. Sin comando (chip "Libre") -> DeepSeek con el texto tal cual.

Los comandos que cambian de planilla (`hoja`, `N planilla`) se descartan: en
la app el chat siempre escribe en la planilla abierta.
"""
from dataclasses import dataclass
from typing import Awaitable, Callable

from accounting.commands.sheet_commands import AdditionalSheetCommand, SelectSheetCommand
from accounting.dispatcher import CommandDispatcher
from accounting.money import cell_number, parse_amount
from config.log import log_error
from mobile.catalog import AMOUNT, NONE, CatalogEntry, find_entry
from mobile.errors import BadGateway, Unprocessable

#: Palabras que, justo después de un número, cambian su valor ("5 mil"):
#: ese texto no se puede leer directo y va a DeepSeek.
_MULTIPLIERS = {
    "mil", "k", "luca", "lucas", "millon", "millón", "millones", "melon", "melones", "palo", "palos",
}
#: Palabras de relleno que se quitan al inicio de la descripción ("5000 de pan").
_CONNECTORS = {"de", "del", "para"}

ExtractCommands = Callable[[str], Awaitable[list[str]]]


@dataclass(frozen=True)
class BuiltCommands:
    commands: list[str]   # lo que se ejecuta, en orden
    rejected: list[str]   # comandos de cambio de planilla que no se ejecutan
    used_ai: bool         # True si pasó por DeepSeek


def _amount(token: str) -> str | None:
    """Monto positivo escrito como número ("5.000", "$1.200.000") en formato del bot."""
    try:
        value = parse_amount(token)
    except ValueError:
        return None
    return str(cell_number(value)) if value > 0 else None


def strict_command(entry: CatalogEntry, text: str) -> str | None:
    """El comando listo si el texto se entiende sin IA; si no, None."""
    tokens = text.split()
    if entry.args == NONE:
        return entry.id
    if entry.args == AMOUNT:
        if len(tokens) != 1:
            return None
        amount = _amount(tokens[0])
        return f"{entry.id} {amount}" if amount is not None else None

    # monto + texto (descripción o nombre del trabajador)
    if len(tokens) < 2:
        return None
    first, last = _amount(tokens[0]), _amount(tokens[-1])
    if first is not None and last is None:
        amount, rest = first, tokens[1:]
    elif last is not None and first is None:
        amount, rest = last, tokens[:-1]
    else:
        return None                       # ninguno o los dos son números: ambiguo
    if any(_amount(token) is not None for token in rest):
        return None                       # "pan 5000 2": ¿cuál es el monto?
    if rest[0].lower() in _MULTIPLIERS:
        return None                       # "5 mil pan" no son 5 pesos
    if rest[0].lower() in _CONNECTORS and len(rest) > 1:
        rest = rest[1:]
    return f"{entry.id} {amount} {' '.join(rest)}"


class CommandBuilder:
    def __init__(self, dispatcher: CommandDispatcher, extract_commands: ExtractCommands):
        self._dispatcher = dispatcher
        self._extract = extract_commands

    async def build(self, command_id: str | None, text: str) -> BuiltCommands:
        text = " ".join((text or "").split())
        if command_id:
            entry = find_entry(command_id)
            if entry is None:
                raise Unprocessable(f"Comando desconocido: '{command_id}'.", "COMANDO_DESCONOCIDO")
            if entry.args != NONE and not text:
                raise Unprocessable(f"Escribe el monto para '{entry.label}'.", "FALTA_TEXTO")
            strict = strict_command(entry, text)
            if strict is not None:
                return BuiltCommands([strict], [], used_ai=False)
            candidates = await self._ask_ai(f"{entry.id} {text}")
        else:
            if not text:
                raise Unprocessable("Escribe un mensaje.", "FALTA_TEXTO")
            candidates = await self._ask_ai(text)

        commands, rejected = [], []
        for command in candidates:
            resolved = self._dispatcher.resolve(command)
            if isinstance(resolved, (SelectSheetCommand, AdditionalSheetCommand)):
                rejected.append(command)
            else:
                commands.append(command)
        return BuiltCommands(commands, rejected, used_ai=True)

    async def _ask_ai(self, text: str) -> list[str]:
        try:
            return await self._extract(text)
        except Exception as error:
            log_error("convirtiendo texto de la app a comandos (DeepSeek)", error, f"text={text!r}")
            raise BadGateway(
                "No se pudo interpretar el mensaje. Intenta de nuevo o escríbelo como "
                "'5.000 pan'.",
                "IA_NO_DISPONIBLE",
            )
