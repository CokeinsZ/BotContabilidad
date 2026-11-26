import { APP } from '@/constants/app';

import { getDatabase } from '../database';

/**
 * Limpieza al abrir la app:
 * - Los mensajes que quedaron "enviando" (la app se cerró a mitad) pasan a "fallido".
 * - Se borran los mensajes de más de 90 días.
 */
export async function limpiarHistorialChat(ahora: number = Date.now()): Promise<void> {
  const db = await getDatabase();
  await db.runAsync("UPDATE mensajes SET estado_envio = 'fallido' WHERE estado_envio = 'enviando'");
  await db.runAsync('DELETE FROM mensajes WHERE creado_en < ?', ahora - APP.chatRetentionMs);
}
