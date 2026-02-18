class UndoService:
    def __init__(self, google_sheets_service):
        self.google_sheets_service = google_sheets_service
        self._last_action = None
        self._command_aliases = {
            "gasto": "expense",
            "g": "expense",
            "trabajador": "worker",
            "trabajadores": "worker",
            "t": "worker",
            "administrador": "admin",
            "admin": "admin",
            "retiro": "withdraw",
            "r": "withdraw",
            "saldo": "balance",
            "saldos": "balance",
            "s": "balance",
            "efectivo": "cash",
            "e": "cash",
            "limpieza": "cleaning",
            "aseo": "cleaning",
            "aseos": "cleaning",
            "l": "cleaning",
            "alimentacion": "feeding",
            "alimentaciones": "feeding",
            "comida": "feeding",
            "a": "feeding",
            "inversiones": "investment",
            "inversion": "investment",
            "inv": "investment",
        }

    def store_last_command(self, command: str, args: list, sheet_id: str):
        canonical = self._command_aliases.get(command)
        if not canonical or not sheet_id:
            return False

        previous_value = None
        if canonical == "balance":
            previous_value = self.google_sheets_service.get_value(sheet_id, "B42")
        elif canonical == "cash":
            previous_value = self.google_sheets_service.get_value(sheet_id, "B39")

        self._last_action = {
            "canonical": canonical,
            "command": command,
            "args": args,
            "sheet_id": sheet_id,
            "previous_value": previous_value,
        }
        return True

    def undo_last_command(self, args=None):
        if not self._last_action:
            return "⚠️ No hay un comando para deshacer."

        action = self._last_action
        sheet_id = action["sheet_id"]
        previous_value = action["previous_value"]
        canonical = action["canonical"]

        if canonical == "expense":
            success = self.google_sheets_service.undo_expense(sheet_id)
        elif canonical == "worker":
            success = self.google_sheets_service.undo_worker_payment(sheet_id)
        elif canonical == "admin":
            success = self.google_sheets_service.undo_admin_expense(sheet_id)
        elif canonical == "withdraw":
            success = self.google_sheets_service.undo_withdraw(sheet_id)
        elif canonical == "cash":
            success = self.google_sheets_service.undo_shift_cash(sheet_id, previous_value)
        elif canonical == "balance":
            success = self.google_sheets_service.undo_generated_cash(sheet_id, previous_value)
        elif canonical == "cleaning":
            success = self.google_sheets_service.undo_cleaning_expense(sheet_id)
        elif canonical == "feeding":
            success = self.google_sheets_service.undo_feeding_expense(sheet_id)
        elif canonical == "investment":
            success = self.google_sheets_service.undo_investment(sheet_id)
        else:
            success = False

        if success:
            command = action["command"]
            args = " ".join(action["args"])
            self._last_action = None
            return f"✅ Se deshizo el ultimo comando: {command} - {args}."

        return "⚠️ No se pudo deshacer el ultimo comando."
