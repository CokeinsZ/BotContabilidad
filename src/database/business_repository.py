"""Repositorio de businesses y administradores (capa de acceso a datos)."""
from database.connection import Database
from database.models import Administrator, Business, BusinessContext


class BusinessRepository:
    """Operaciones de lectura/escritura sobre businesses y administradores."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def find_context_by_phone(self, phone_number: str) -> BusinessContext | None:
        """Devuelve el business y administrador asociados a un teléfono.

        Es la consulta central del bot: permite que un mismo bot atienda a
        múltiples empresas identificando al remitente del mensaje.
        """
        row = (
            self._db.connect()
            .execute(
                """
                SELECT
                    b.id   AS b_id,  b.name AS b_name,  b.sheets_folder_id, b.state AS b_state,
                    a.id   AS a_id,  a.name AS a_name,  a.phone_number,     a.state AS a_state,
                    a.business_id
                FROM business_administrators a
                INNER JOIN businesses b ON b.id = a.business_id
                WHERE a.phone_number = ?
                  AND a.state = 'active'
                  AND b.state = 'active'
                LIMIT 1
                """,
                (phone_number,),
            )
            .fetchone()
        )
        if row is None:
            return None

        business = Business(
            id=row["b_id"],
            name=row["b_name"],
            sheets_folder_id=row["sheets_folder_id"],
            state=row["b_state"],
        )
        administrator = Administrator(
            id=row["a_id"],
            business_id=row["business_id"],
            name=row["a_name"],
            phone_number=row["phone_number"],
            state=row["a_state"],
        )
        return BusinessContext(business=business, administrator=administrator)

    def find_by_id(self, business_id: int) -> Business | None:
        row = (
            self._db.connect()
            .execute(
                "SELECT id, name, sheets_folder_id, state FROM businesses WHERE id = ?",
                (business_id,),
            )
            .fetchone()
        )
        return self._to_business(row)

    def list_all(self) -> list[Business]:
        rows = (
            self._db.connect()
            .execute("SELECT id, name, sheets_folder_id, state FROM businesses ORDER BY id")
            .fetchall()
        )
        return [self._to_business(row) for row in rows]

    def list_administrators(self, business_id: int) -> list[Administrator]:
        rows = (
            self._db.connect()
            .execute(
                """
                SELECT id, business_id, name, phone_number, state
                FROM business_administrators
                WHERE business_id = ?
                ORDER BY id
                """,
                (business_id,),
            )
            .fetchall()
        )
        return [self._to_administrator(row) for row in rows]

    # ------------------------------------------------------------------
    # Escrituras
    # ------------------------------------------------------------------
    def create_business(self, name: str, sheets_folder_id: str) -> Business:
        connection = self._db.connect()
        cursor = connection.execute(
            "INSERT INTO businesses (name, sheets_folder_id) VALUES (?, ?)",
            (name, sheets_folder_id),
        )
        connection.commit()
        return self.find_by_id(cursor.lastrowid)

    def create_administrator(
        self, business_id: int, name: str, phone_number: str
    ) -> Administrator:
        connection = self._db.connect()
        cursor = connection.execute(
            """
            INSERT INTO business_administrators (business_id, name, phone_number)
            VALUES (?, ?, ?)
            """,
            (business_id, name, phone_number),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, business_id, name, phone_number, state
            FROM business_administrators WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        return self._to_administrator(row)

    # ------------------------------------------------------------------
    # Mappers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_business(row) -> Business | None:
        if row is None:
            return None
        return Business(
            id=row["id"],
            name=row["name"],
            sheets_folder_id=row["sheets_folder_id"],
            state=row["state"],
        )

    @staticmethod
    def _to_administrator(row) -> Administrator | None:
        if row is None:
            return None
        return Administrator(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            phone_number=row["phone_number"],
            state=row["state"],
        )
