import type { Perfil, Sesion } from '@/api';

/** restaurando = leyendo la sesión guardada al abrir la app (el splash sigue visible). */
export type EstadoSesion = 'restaurando' | 'sinSesion' | 'conSesion';

export interface SessionValue {
  estado: EstadoSesion;
  /** Administrador de la sesión (filtra el historial local del chat). */
  administradorId: number | null;
  /** Último perfil conocido (sirve para abrir la app sin red). */
  perfilGuardado: Perfil | null;
  /** Termina la vinculación: guarda la sesión y entra a la app. */
  completarVinculacion: (sesion: Sesion) => Promise<void>;
  /** Nunca falla: aunque no haya red, la sesión se cierra en el teléfono. */
  cerrarSesion: () => Promise<void>;
  /** Guarda el perfil actualizado (p. ej. tras cambiar un nombre). */
  recordarPerfil: (perfil: Perfil) => Promise<void>;
}
