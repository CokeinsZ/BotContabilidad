export interface Administrador {
  id: number;
  nombre: string;
  /** Teléfono o LID de WhatsApp con el que lo conoce el bot. */
  identificador: string;
}

/** Otro administrador del mismo negocio (o el propio, con `esUsted`). */
export interface Companero {
  id: number;
  nombre: string;
  esUsted: boolean;
}
