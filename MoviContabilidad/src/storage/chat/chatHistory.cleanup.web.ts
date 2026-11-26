import { APP } from '@/constants/app';

import { modificarAlmacen } from './chatHistory.localStore';

/** Lo mismo que chatHistory.cleanup.ts, sobre el historial de `localStorage`. */
export async function limpiarHistorialChat(ahora: number = Date.now()): Promise<void> {
  modificarAlmacen((almacen) => {
    almacen.filas = almacen.filas.filter((fila) => fila.creado_en >= ahora - APP.chatRetentionMs);
    for (const fila of almacen.filas) {
      if (fila.estado_envio === 'enviando') fila.estado_envio = 'fallido';
    }
  });
}
