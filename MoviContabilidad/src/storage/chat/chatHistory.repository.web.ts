/**
 * Versión web del historial del chat (misma API que chatHistory.repository.ts):
 * guardado en `localStorage` de este navegador, nunca en el servidor.
 */
import type { EstadoEnvio, Mensaje, RespuestaBot } from '@/api';

import { leerAlmacen, modificarAlmacen } from './chatHistory.localStore';
import { filaAMensaje, type MensajePropio } from './chatHistory.types';

export type { MensajePropio } from './chatHistory.types';

export async function guardarMensajePropio(mensaje: MensajePropio, ahora: number = Date.now()): Promise<void> {
  modificarAlmacen((almacen) => {
    if (almacen.filas.some((fila) => fila.client_id === mensaje.clientId)) {
      throw new Error(`client_id repetido: ${mensaje.clientId}`); // como el índice único de SQLite
    }
    almacen.filas.push({
      id: almacen.siguienteId++,
      administrador_id: mensaje.administradorId,
      planilla_id: mensaje.planillaId,
      client_id: mensaje.clientId,
      autor: 'yo',
      comando: mensaje.comando,
      texto: mensaje.texto,
      tipo: 'enviado',
      estado_envio: 'enviando',
      responde_a: null,
      creado_en: ahora,
    });
  });
}

export async function marcarEstadoEnvio(clientId: string, estado: EstadoEnvio): Promise<void> {
  modificarAlmacen((almacen) => {
    for (const fila of almacen.filas) {
      if (fila.client_id === clientId) fila.estado_envio = estado;
    }
  });
}

export async function guardarRespuestas(
  administradorId: number,
  planillaId: string,
  respondeA: string | null,
  respuestas: RespuestaBot[],
  ahora: number = Date.now(),
): Promise<void> {
  if (respuestas.length === 0) return;
  modificarAlmacen((almacen) => {
    respuestas.forEach((respuesta, index) => {
      almacen.filas.push({
        id: almacen.siguienteId++,
        administrador_id: administradorId,
        planilla_id: planillaId,
        client_id: null,
        autor: 'bot',
        comando: null,
        texto: respuesta.texto,
        tipo: respuesta.tipo,
        estado_envio: null,
        responde_a: respondeA,
        creado_en: ahora + index,
      });
    });
  });
}

/** Mensajes del más nuevo al más viejo (para una FlatList invertida). */
export async function listarMensajes(
  administradorId: number,
  planillaId: string,
  { antesDe, limite }: { antesDe?: number; limite: number },
): Promise<Mensaje[]> {
  return leerAlmacen()
    .filas.filter(
      (fila) =>
        fila.administrador_id === administradorId &&
        fila.planilla_id === planillaId &&
        (antesDe === undefined || fila.id < antesDe),
    )
    .sort((a, b) => b.id - a.id)
    .slice(0, limite)
    .map(filaAMensaje);
}

export async function borrarHistorial(administradorId: number): Promise<void> {
  modificarAlmacen((almacen) => {
    almacen.filas = almacen.filas.filter((fila) => fila.administrador_id !== administradorId);
  });
}
