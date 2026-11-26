import type { Administrador, Companero } from './administrador';

export interface Negocio {
  id: number;
  nombre: string;
  carpetaPlanillasUrl: string;
  carpetaTrabajadoresUrl: string | null;
}

export interface Perfil {
  administrador: Administrador;
  negocio: Negocio;
  administradores: Companero[];
  /** Hoy en la zona horaria del negocio (dd-mm-aaaa), según el servidor. */
  hoy: string;
  googleConectado: boolean;
  whatsappBot: string | null;
}
