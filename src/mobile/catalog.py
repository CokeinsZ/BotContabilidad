"""Catálogo de comandos para la banda del chat de la app.

Los comandos los define el dispatcher; aquí solo van los datos de interfaz
(etiqueta, ícono, ejemplo, qué argumentos pide). Una prueba verifica que cada
`id` exista en el dispatcher: si alguien renombra un comando, se entera.

`hoja` y `N planilla` no están: en la app las planillas se crean y se eligen
en sus propias pantallas. `instrucciones` tampoco: la app tiene pantalla de Ayuda.
"""
from dataclasses import dataclass

from accounting.dispatcher import CommandDispatcher

NONE = "ninguno"
AMOUNT = "monto"
AMOUNT_TEXT = "monto_texto"
AMOUNT_WORKER = "monto_trabajador"


@dataclass(frozen=True)
class CatalogEntry:
    id: str                       # nombre del comando en el dispatcher
    label: str
    icon: str                     # nombre semántico; la app lo traduce a su ícono
    args: str                     # NONE | AMOUNT | AMOUNT_TEXT | AMOUNT_WORKER
    example: str
    help: str
    confirm: bool = False         # pedir confirmación antes de enviar
    suggests_worker: bool = False # sugerir nombres de trabajadores al escribir


#: En el orden de la banda (por frecuencia de uso).
CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry("gasto", "Gasto", "gasto", AMOUNT_TEXT, "5.000 pan", "Compras a proveedores"),
    CatalogEntry("efectivo", "Efectivo", "efectivo", AMOUNT, "350.000", "Efectivo de las ventas del día"),
    CatalogEntry("saldo", "Saldo", "saldo", AMOUNT, "1.200.000", "Dinero físico en caja"),
    CatalogEntry("trabajador", "Vale", "prestamo", AMOUNT_WORKER, "20.000 juan",
                 "Vale (préstamo) a un trabajador: también queda en su archivo", suggests_worker=True),
    CatalogEntry("retiro", "Retiro", "retiro", AMOUNT_TEXT, "100.000 banco",
                 "Sacar dinero de la caja. 'nomina <nombre>' también cierra el período"),
    CatalogEntry("limpieza", "Aseo", "aseo", AMOUNT, "8.000", "Productos de aseo y limpieza"),
    CatalogEntry("alimentacion", "Alimentación", "alimentacion", AMOUNT, "30.000", "Comida del personal"),
    CatalogEntry("administrador", "Vale admin", "administrador", AMOUNT, "20.000", "Vale del administrador"),
    CatalogEntry("inversion", "Inversión", "inversion", AMOUNT_TEXT, "500.000 maquinaria",
                 "Inversiones en el negocio"),
    CatalogEntry("nomina", "Nómina", "nomina", AMOUNT_WORKER, "200.000 juan",
                 "Pago de nómina: cierra los préstamos del trabajador", suggests_worker=True),
    CatalogEntry("terminar_dia", "Resumen", "resumen", NONE, "", "Totales de la planilla"),
    CatalogEntry("deshacer", "Deshacer", "deshacer", NONE, "", "Revierte todo lo de tu último mensaje",
                 confirm=True),
    CatalogEntry("corregir_saldos", "Corregir saldos", "corregir_saldos", NONE, "",
                 "Recalcula el saldo de todas las planillas siguientes a esta", confirm=True),
)

_BY_ID = {entry.id: entry for entry in CATALOG}


def find_entry(command_id: str | None) -> CatalogEntry | None:
    return _BY_ID.get((command_id or "").strip().lower())


def aliases_of(dispatcher: CommandDispatcher, entry: CatalogEntry) -> list[str]:
    """Alias que también entiende el bot (para la pantalla de Ayuda)."""
    command = dispatcher.resolve(entry.id)
    return list(command.aliases) if command is not None else []
