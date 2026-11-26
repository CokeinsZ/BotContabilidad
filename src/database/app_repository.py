"""Persistencia de la app móvil: vinculaciones y sesiones.

El historial del chat NO se guarda en el servidor: cada teléfono lo guarda en
su propio SQLite. Aquí solo vive lo necesario para autenticar.

Todos los tiempos son segundos Unix (UTC) en INTEGER.
"""
from dataclasses import dataclass

from database.connection import Database

PENDING = "pending"
CONFIRMED = "confirmed"
CONSUMED = "consumed"


@dataclass(frozen=True)
class PairingRecord:
    id: str
    code: str
    device_name: str | None
    administrator_id: int | None
    state: str
    expires_at: int
    created_at: int


@dataclass(frozen=True)
class SessionRecord:
    id: int
    administrator_id: int
    device_name: str | None
    created_at: int
    last_used_at: int
    expires_at: int
    revoked_at: int | None

    def is_active(self, now: int) -> bool:
        return self.revoked_at is None and self.expires_at > now


class AppRepository:
    """Lecturas y escrituras de las tablas `app_pairings` y `app_sessions`."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Vinculaciones
    # ------------------------------------------------------------------
    def create_pairing(
        self, pairing_id: str, code: str, device_name: str | None, expires_at: int, now: int
    ) -> None:
        connection = self._db.connect()
        connection.execute(
            """
            INSERT INTO app_pairings (id, code, device_name, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pairing_id, code, device_name, expires_at, now),
        )
        connection.commit()

    def code_in_use(self, code: str, now: int) -> bool:
        """True si hay una vinculación pendiente y vigente con ese código."""
        row = (
            self._db.connect()
            .execute(
                "SELECT 1 FROM app_pairings WHERE code = ? AND state = ? AND expires_at > ? LIMIT 1",
                (code, PENDING, now),
            )
            .fetchone()
        )
        return row is not None

    def get_pairing(self, pairing_id: str) -> PairingRecord | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM app_pairings WHERE id = ?", (pairing_id,))
            .fetchone()
        )
        return self._to_pairing(row)

    def confirm_pairing(self, code: str, administrator_id: int, now: int) -> PairingRecord | None:
        """Confirma la vinculación pendiente y vigente con ese código.

        Devuelve la vinculación confirmada, o None si el código no existe, ya
        se usó o venció.
        """
        connection = self._db.connect()
        row = connection.execute(
            """
            SELECT * FROM app_pairings
            WHERE code = ? AND state = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (code, PENDING, now),
        ).fetchone()
        if row is None:
            return None
        cursor = connection.execute(
            "UPDATE app_pairings SET state = ?, administrator_id = ? WHERE id = ? AND state = ?",
            (CONFIRMED, administrator_id, row["id"], PENDING),
        )
        connection.commit()
        if cursor.rowcount != 1:
            return None
        return self.get_pairing(row["id"])

    def consume_pairing(self, pairing_id: str) -> bool:
        """Marca como consumida una vinculación confirmada.

        Solo una consulta puede ganar: así los tokens se entregan una única
        vez aunque la app consulte dos veces al mismo tiempo.
        """
        connection = self._db.connect()
        cursor = connection.execute(
            "UPDATE app_pairings SET state = ? WHERE id = ? AND state = ?",
            (CONSUMED, pairing_id, CONFIRMED),
        )
        connection.commit()
        return cursor.rowcount == 1

    def delete_expired_pairings(self, now: int) -> None:
        """Borra las vinculaciones vencidas hace más de un día (limpieza)."""
        connection = self._db.connect()
        connection.execute("DELETE FROM app_pairings WHERE expires_at < ?", (now - 86_400,))
        connection.commit()

    # ------------------------------------------------------------------
    # Sesiones
    # ------------------------------------------------------------------
    def create_session(
        self, administrator_id: int, refresh_token_hash: str, device_name: str | None,
        expires_at: int, now: int,
    ) -> int:
        connection = self._db.connect()
        cursor = connection.execute(
            """
            INSERT INTO app_sessions
                (administrator_id, refresh_token_hash, device_name, created_at, last_used_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (administrator_id, refresh_token_hash, device_name, now, now, expires_at),
        )
        connection.commit()
        return cursor.lastrowid

    def get_session(self, session_id: int) -> SessionRecord | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM app_sessions WHERE id = ?", (session_id,))
            .fetchone()
        )
        return self._to_session(row)

    def find_session_by_refresh_hash(self, refresh_token_hash: str) -> SessionRecord | None:
        row = (
            self._db.connect()
            .execute("SELECT * FROM app_sessions WHERE refresh_token_hash = ?", (refresh_token_hash,))
            .fetchone()
        )
        return self._to_session(row)

    def rotate_refresh(
        self, session_id: int, old_hash: str, new_hash: str, expires_at: int, now: int
    ) -> bool:
        """Reemplaza el refresh token si sigue siendo `old_hash` (un uso por token)."""
        connection = self._db.connect()
        cursor = connection.execute(
            """
            UPDATE app_sessions
            SET refresh_token_hash = ?, expires_at = ?, last_used_at = ?
            WHERE id = ? AND refresh_token_hash = ? AND revoked_at IS NULL
            """,
            (new_hash, expires_at, now, session_id, old_hash),
        )
        connection.commit()
        return cursor.rowcount == 1

    def revoke_session(self, session_id: int, now: int) -> None:
        connection = self._db.connect()
        connection.execute(
            "UPDATE app_sessions SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL",
            (now, session_id),
        )
        connection.commit()

    def revoke_sessions_of_admin(self, administrator_id: int, now: int) -> int:
        """Revoca todas las sesiones activas de un administrador. Devuelve cuántas."""
        connection = self._db.connect()
        cursor = connection.execute(
            """
            UPDATE app_sessions SET revoked_at = ?
            WHERE administrator_id = ? AND revoked_at IS NULL AND expires_at > ?
            """,
            (now, administrator_id, now),
        )
        connection.commit()
        return cursor.rowcount

    # ------------------------------------------------------------------
    # Mappers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_pairing(row) -> PairingRecord | None:
        if row is None:
            return None
        return PairingRecord(
            id=row["id"],
            code=row["code"],
            device_name=row["device_name"],
            administrator_id=row["administrator_id"],
            state=row["state"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _to_session(row) -> SessionRecord | None:
        if row is None:
            return None
        return SessionRecord(
            id=row["id"],
            administrator_id=row["administrator_id"],
            device_name=row["device_name"],
            created_at=row["created_at"],
            last_used_at=row["last_used_at"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )
