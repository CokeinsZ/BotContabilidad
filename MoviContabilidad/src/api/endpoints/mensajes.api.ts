/**
 * Chat de una planilla. El historial NO viene del servidor: lo guarda el teléfono.
 * - GET    /app/planillas/{id}/estado      -> pregunta pendiente y qué deshace "Deshacer"
 * - POST   /app/planillas/{id}/mensajes    -> respuestas del bot (mismo client_id = mismo resultado)
 * - POST   /app/planillas/{id}/seleccion   -> responde la pregunta pendiente
 * - DELETE /app/planillas/{id}/seleccion   -> la cancela
 */
import { CHAT_TIMEOUT_MS } from '../client/config';
import { request } from '../client/http';
import type { EstadoChatDto, ResultadoChatDto } from '../dto/mensajes.dto';
import type { EstadoChat, ResultadoChat } from '../entities';
import { toEstadoChat, toResultadoChat } from '../mappers/mensajes.mapper';

const base = (planillaId: string) => `/planillas/${encodeURIComponent(planillaId)}`;

export interface MensajeSaliente {
  clientId: string;
  comando: string | null;
  texto: string;
}

export async function obtenerEstadoChat(planillaId: string): Promise<EstadoChat> {
  return toEstadoChat(await request<EstadoChatDto>(`${base(planillaId)}/estado`));
}

export async function enviarMensaje(planillaId: string, mensaje: MensajeSaliente): Promise<ResultadoChat> {
  const dto = await request<ResultadoChatDto>(`${base(planillaId)}/mensajes`, {
    method: 'POST',
    body: { client_id: mensaje.clientId, comando: mensaje.comando, texto: mensaje.texto },
    timeoutMs: CHAT_TIMEOUT_MS,
  });
  return toResultadoChat(dto);
}

export async function responderSeleccion(planillaId: string, opcion: number): Promise<ResultadoChat> {
  const dto = await request<ResultadoChatDto>(`${base(planillaId)}/seleccion`, {
    method: 'POST',
    body: { opcion },
    timeoutMs: CHAT_TIMEOUT_MS,
  });
  return toResultadoChat(dto);
}

export async function cancelarSeleccion(planillaId: string): Promise<ResultadoChat> {
  const dto = await request<ResultadoChatDto>(`${base(planillaId)}/seleccion`, {
    method: 'DELETE',
    timeoutMs: CHAT_TIMEOUT_MS,
  });
  return toResultadoChat(dto);
}
