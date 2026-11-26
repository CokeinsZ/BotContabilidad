/**
 * Migraciones del SQLite local del teléfono (patrón de la documentación de
 * expo-sqlite: `PRAGMA user_version`). Cada paso corre una sola vez y en orden.
 */
import type { SQLiteDatabase } from 'expo-sqlite';

const MIGRATIONS: string[] = [
  // v1: historial del chat (nunca se guarda en el servidor).
  `
  CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    administrador_id INTEGER NOT NULL,
    planilla_id TEXT NOT NULL,
    client_id TEXT,
    autor TEXT NOT NULL CHECK (autor IN ('yo', 'bot')),
    comando TEXT,
    texto TEXT NOT NULL,
    tipo TEXT NOT NULL,
    estado_envio TEXT,
    responde_a TEXT,
    creado_en INTEGER NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_mensajes_planilla ON mensajes (administrador_id, planilla_id, id);
  CREATE UNIQUE INDEX IF NOT EXISTS idx_mensajes_client ON mensajes (client_id) WHERE client_id IS NOT NULL;
  `,
];

export const DATABASE_VERSION = MIGRATIONS.length;

export async function migrate(db: SQLiteDatabase): Promise<void> {
  const row = await db.getFirstAsync<{ user_version: number }>('PRAGMA user_version');
  let version = row?.user_version ?? 0;
  if (version >= DATABASE_VERSION) return;
  if (version === 0) {
    await db.execAsync("PRAGMA journal_mode = 'wal';");
  }
  while (version < DATABASE_VERSION) {
    await db.execAsync(MIGRATIONS[version]);
    version += 1;
    await db.execAsync(`PRAGMA user_version = ${version}`);
  }
}
