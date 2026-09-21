"""Comando de ayuda del bot."""
from accounting.commands.base import Command, CommandContext


class HelpCommand(Command):
    """`instrucciones`: muestra la ayuda de uso del bot."""

    name = "instrucciones"
    aliases = ("i", "help")

    def execute(self, ctx: CommandContext, args: list[str]) -> str:
        folder_url = (
            f"https://drive.google.com/drive/folders/{ctx.business.sheets_folder_id}"
        )
        return f"""
            Bienvenido al Bot de Contabilidad de {ctx.business.name}. \n
            Link a la carpeta: {folder_url} \n
            Instrucciones de uso:\n
            1. Seleccionar o crear una hoja, usando el comando: \n
             'hoja <fecha>' \n
             1.1. Para crear una planilla adicional del mismo día: \n
                'segunda planilla', 'tercera planilla', '2 planilla', ...\n
            2. Ejecutar la acción que desees: \n
             2.1. Para agregar un gasto: \n
                'gasto <monto> <descripcion>'\n

             2.2. Para registrar un préstamo a un trabajador: \n
                'trabajador <monto> <nombre>'\n

             2.3. Para agregar un vale del administrador: \n
                'administrador <monto>'\n

             2.4. Para agregar un retiro de efectivo: \n
                'retiro <monto> <descripcion>'\n
                Si la descripcion es 'nomina <nombre>', además cierra el período del trabajador.\n

             2.4.1. Para pagar la nómina de un trabajador (cierra sus préstamos): \n
                'nomina <monto> <nombre>'\n

             2.5. Para registrar el saldo de efectivo: \n
                'saldo <monto>'\n

             2.6. Para agregar un el efectivo del dia: \n
                'efectivo <monto>'\n

             2.7. Para terminar el dia, y actualizar la hoja de resumen de ventas: \n
             'terminar_dia' \n

             2.8. Para ver las instrucciones de uso: \n
                'instrucciones' \n
                
             2.9. Para deshacer el ultimo comando: \n
                'deshacer' \n

            3. Al finalizar, ejecutar el comando 'terminar_dia' para ver el resumen de ventas. \n
        
            ¡Gracias por usar el Bot de Contabilidad!
        """
