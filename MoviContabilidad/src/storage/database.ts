/**
 * Base de datos local del teléfono. Se abre una sola vez y se migra al abrir.
 * Los repositorios piden la conexión con `getDatabase()`.
 */
import { openDatabaseAsync, type SQLiteDatabase } from 'expo-sqlite';

import { migrate } from './migrations';

const DATABASE_NAME = 'movicontabilidad.db';

let opening: Promise<SQLiteDatabase> | null = null;

export function getDatabase(): Promise<SQLiteDatabase> {
  opening ??= openDatabaseAsync(DATABASE_NAME).then(async (db) => {
    await migrate(db);
    return db;
  });
  return opening;
}
