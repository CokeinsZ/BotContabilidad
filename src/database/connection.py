"""
Gestión de la conexión a la base de datos SQLite.

SQLite no permite compartir una conexión entre hilos de forma segura, por lo
que este módulo entrega una conexión por hilo (`threading.local`). El esquema
se inicializa desde el archivo SQL declarado en la configuración.
"""
import sqlite3
import threading
from pathlib import Path


class Database:
    """Administra conexiones SQLite por hilo e inicializa el esquema."""

    def __init__(self, db_path: Path, schema_path: Path):
        self._db_path = db_path
        self._local = threading.local()

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_schema(schema_path)

    def _run_schema(self, schema_path: Path) -> None:
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            schema_sql = schema_file.read()
        connection = self.connect()
        connection.executescript(schema_sql)
        connection.commit()
        self._run_migrations(connection)

    def _run_migrations(self, connection: sqlite3.Connection) -> None:
        """Migraciones idempotentes para bases de datos ya existentes.

        `CREATE TABLE IF NOT EXISTS` no actualiza tablas viejas: si una tabla
        ya existía cuando se agregó una columna nueva al esquema, hay que
        hacer el ALTER TABLE manualmente. Cada entrada es idempotente.
        """
        migrations = [
            # (tabla, columna, DDL si falta la columna)
            (
                "businesses",
                "workers_folder_id",
                "ALTER TABLE businesses ADD COLUMN workers_folder_id TEXT",
            ),
        ]
        for table, column, ddl in migrations:
            columns = {
                row[1] for row in connection.execute(f"PRAGMA table_info({table})")
            }
            if column not in columns:
                connection.execute(ddl)
                connection.commit()

    def connect(self) -> sqlite3.Connection:
        """Devuelve la conexión del hilo actual, creándola si es necesario."""
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(str(self._db_path))
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection = connection
        return connection
