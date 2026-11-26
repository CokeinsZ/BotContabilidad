import { limpiarHistorialChat } from './chat/chatHistory.cleanup';
import { getDatabase } from './database';

/** Abre y migra la base local y limpia el historial. Nunca rompe el arranque. */
export async function prepararAlmacenamiento(): Promise<void> {
  try {
    await getDatabase();
    await limpiarHistorialChat();
  } catch (error) {
    console.warn('No se pudo preparar la base de datos local', error);
  }
}
