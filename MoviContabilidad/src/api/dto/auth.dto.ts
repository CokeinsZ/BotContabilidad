import type { PerfilDto } from './perfil.dto';

export interface SesionDto {
  access_token: string;
  expira_en: number;
  refresh_token: string;
  perfil: PerfilDto;
}

export interface VinculacionDto {
  vinculacion_id: string;
  codigo: string;
  mensaje: string;
  whatsapp_url: string | null;
  expira_en: number;
}

export interface EstadoVinculacionDto {
  estado: 'pendiente' | 'confirmada' | 'consumida' | 'expirada';
  sesion: SesionDto | null;
}
