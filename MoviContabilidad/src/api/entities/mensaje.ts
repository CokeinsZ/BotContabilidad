export type TipoRespuesta = 'exito' | 'aviso' | 'error' | 'info' | 'seleccion';

export interface RespuestaBot {
  tipo: TipoRespuesta;
  texto: string;
}

export interface OpcionSeleccion {
  valor: number;
  etiqueta: string;
  crea: boolean;
}

/** Pregunta pendiente del bot (p. ej. en cuál archivo guardar un préstamo). */
export interface Seleccion {
  pregunta: string;
  opciones: OpcionSeleccion[];
  /** Lo que se cancela si no se responde: "trabajador 20000 jose". */
  comando: string;
  planillaId: string | null;
  planillaNombre: string | null;
}

export interface EstadoChat {
  seleccion: Seleccion | null;
  /** Qué revertiría "Deshacer" (null = nada). */
  deshacer: string | null;
}

export interface ResultadoChat {
  clientId: string | null;
  comandos: string[];
  interpretadoPorIa: boolean;
  respuestas: RespuestaBot[];
  estado: EstadoChat;
  procesadoEn: string;
}

/** Mensaje del historial del chat, guardado SOLO en el teléfono (src/storage). */
export type TipoMensaje = 'enviado' | TipoRespuesta;
export type EstadoEnvio = 'enviando' | 'enviado' | 'fallido';

export interface Mensaje {
  id: number;
  planillaId: string;
  clientId: string | null;
  autor: 'yo' | 'bot';
  /** Comando elegido en la banda (null = texto libre o respuesta del bot). */
  comando: string | null;
  texto: string;
  tipo: TipoMensaje;
  estadoEnvio: EstadoEnvio | null;
  /** client_id del mensaje propio que originó esta respuesta. */
  respondeA: string | null;
  /** Milisegundos Unix. */
  creadoEn: number;
}
