import type { Perfil } from './negocio';

export interface Sesion {
  accessToken: string;
  /** Segundos de vida del token de acceso. */
  expiraEn: number;
  refreshToken: string;
  perfil: Perfil;
}

export interface Vinculacion {
  id: string;
  codigo: string;
  /** Lo que el administrador envía al bot: "VINCULAR 482913". */
  mensaje: string;
  whatsappUrl: string | null;
  /** Instante (ms) en que vence el código. */
  venceEn: number;
}

export type EstadoVinculacion = 'pendiente' | 'confirmada' | 'consumida' | 'expirada';

export interface ConsultaVinculacion {
  estado: EstadoVinculacion;
  sesion: Sesion | null;
}
