import { limpiarHistorialChat } from './chat/chatHistory.cleanup';

/** En la web no hay base que abrir ni migrar: solo se limpia el historial. */
export async function prepararAlmacenamiento(): Promise<void> {
  try {
    await limpiarHistorialChat();
  } catch (error) {
    console.warn('No se pudo limpiar el historial local', error);
  }
}
