import type { EstadoEnvio, Mensaje, TipoMensaje } from '@/api';

/** Lo que el administrador envía (se guarda en estado "enviando"). */
export interface MensajePropio {
  administradorId: number;
  planillaId: string;
  clientId: string;
  comando: string | null;
  texto: string;
}

/** Fila de la tabla `mensajes` tal como la devuelve SQLite (en la web, igual en JSON). */
export interface FilaMensaje {
  id: number;
  administrador_id: number;
  planilla_id: string;
  client_id: string | null;
  autor: 'yo' | 'bot';
  comando: string | null;
  texto: string;
  tipo: TipoMensaje;
  estado_envio: EstadoEnvio | null;
  responde_a: string | null;
  creado_en: number;
}

export function filaAMensaje(fila: FilaMensaje): Mensaje {
  return {
    id: fila.id,
    planillaId: fila.planilla_id,
    clientId: fila.client_id,
    autor: fila.autor,
    comando: fila.comando,
    texto: fila.texto,
    tipo: fila.tipo,
    estadoEnvio: fila.estado_envio,
    respondeA: fila.responde_a,
    creadoEn: fila.creado_en,
  };
}
