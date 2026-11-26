"""Comando de ayuda del bot."""
from accounting.commands.base import Command, CommandContext


class HelpCommand(Command):
    """`instrucciones`: muestra la ayuda de uso del bot."""

    name = "instrucciones"
    aliases = ("i", "help", "ayuda")

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        folder_url = (
            f"https://drive.google.com/drive/folders/{ctx.business.sheets_folder_id}"
        )
        return "\n".join([
            f"Bienvenido al Bot de Contabilidad de {ctx.business.name}.",
            f"Carpeta de planillas: {folder_url}",
            "",
            "1. Selecciona o crea la planilla del día:",
            "   • hoja <dd-mm-aaaa>",
            "   • segunda planilla / tercera planilla / 2 planilla ... (planillas adicionales del día)",
            "",
            "2. Registra movimientos:",
            "   • gasto <monto> <descripción> — compras a proveedores",
            "   • limpieza <monto> — productos de aseo",
            "   • alimentacion <monto> — comida del personal",
            "   • trabajador <monto> <nombre> — préstamo a un trabajador",
            "   • nomina <monto> <nombre> — pago de nómina (cierra los préstamos del trabajador)",
            "   • administrador <monto> — vale del administrador",
            "   • retiro <monto> <descripción> — sacar dinero de la caja",
            "     (si la descripción es 'nomina <nombre>' también cierra el período del trabajador)",
            "   • inversion <monto> <descripción> — inversiones en el negocio",
            "   • saldo <monto> — dinero físico en caja",
            "   • efectivo <monto> — efectivo de ventas del día",
            "",
            "3. Otros:",
            "   • terminar_dia — resumen del día con el link a la planilla",
            "   • corregir_saldos — recalcula el saldo de todas las planillas siguientes a la "
            "seleccionada (úsalo si corriges una planilla anterior)",
            "   • deshacer — revierte todo lo que hizo tu último mensaje",
            "   • instrucciones — muestra esta ayuda",
            "",
            "Puedes escribir o mandar audio en lenguaje natural, y varios movimientos "
            "en un mismo mensaje (ej: \"gasto 5000 pan y 3000 leche\").",
        ])
