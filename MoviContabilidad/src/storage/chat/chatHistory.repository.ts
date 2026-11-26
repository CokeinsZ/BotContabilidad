/**
 * Historial del chat de cada planilla, guardado SOLO en este teléfono.
 *
 * Se filtra siempre por administrador: si otra persona vincula la app en el
 * mismo teléfono, no ve lo que escribió la anterior.
 */
import type { EstadoEnvio, Mensaje, RespuestaBot } from '@/api';

import { getDatabase } from '../database';
import { filaAMensaje, type FilaMensaje } from './chatHistory.types';

export interface MensajePropio {
  administradorId: number;
  planillaId: string;
  clientId: string;
  comando: string | null;
  texto: string;
}

/** Guarda lo que el administrador envía, en estado "enviando". */
export async function guardarMensajePropio(mensaje: MensajePropio, ahora: number = Date.now()): Promise<void> {
  const db = await getDatabase();
  await db.runAsync(
    `INSERT INTO mensajes (administrador_id, planilla_id, client_id, autor, comando, texto, tipo, estado_envio, creado_en)
     VALUES (?, ?, ?, 'yo', ?, ?, 'enviado', 'enviando', ?)`,
    mensaje.administradorId, mensaje.planillaId, mensaje.clientId, mensaje.comando, mensaje.texto, ahora,
  );
}

export async function marcarEstadoEnvio(clientId: string, estado: EstadoEnvio): Promise<void> {
  const db = await getDatabase();
  await db.runAsync('UPDATE mensajes SET estado_envio = ? WHERE client_id = ?', estado, clientId);
}

/** Guarda las respuestas del bot en una sola transacción. */
export async function guardarRespuestas(
  administradorId: number,
  planillaId: string,
  respondeA: string | null,
  respuestas: RespuestaBot[],
  ahora: number = Date.now(),
): Promise<void> {
  if (respuestas.length === 0) return;
  const db = await getDatabase();
  await db.withTransactionAsync(async () => {
    for (const [index, respuesta] of respuestas.entries()) {
      await db.runAsync(
        `INSERT INTO mensajes (administrador_id, planilla_id, autor, texto, tipo, responde_a, creado_en)
         VALUES (?, ?, 'bot', ?, ?, ?, ?)`,
        administradorId, planillaId, respuesta.texto, respuesta.tipo, respondeA, ahora + index,
      );
    }
  });
}

/** Mensajes del más nuevo al más viejo (para una FlatList invertida). */
export async function listarMensajes(
  administradorId: number,
  planillaId: string,
  { antesDe, limite }: { antesDe?: number; limite: number },
): Promise<Mensaje[]> {
  const db = await getDatabase();
  const filas = antesDe === undefined
    ? await db.getAllAsync<FilaMensaje>(
        'SELECT * FROM mensajes WHERE administrador_id = ? AND planilla_id = ? ORDER BY id DESC LIMIT ?',
        administradorId, planillaId, limite,
      )
    : await db.getAllAsync<FilaMensaje>(
        'SELECT * FROM mensajes WHERE administrador_id = ? AND planilla_id = ? AND id < ? ORDER BY id DESC LIMIT ?',
        administradorId, planillaId, antesDe, limite,
      );
  return filas.map(filaAMensaje);
}

export async function borrarHistorial(administradorId: number): Promise<void> {
  const db = await getDatabase();
  await db.runAsync('DELETE FROM mensajes WHERE administrador_id = ?', administradorId);
}
