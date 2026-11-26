/** Forma exacta del JSON de /app/perfil (src/mobile/dto.py del bot). */
export interface AdministradorDto {
  id: number;
  nombre: string;
  identificador: string;
}

export interface CompaneroDto {
  id: number;
  nombre: string;
  es_usted: boolean;
}

export interface NegocioDto {
  id: number;
  nombre: string;
  carpeta_planillas_url: string;
  carpeta_trabajadores_url: string | null;
}

export interface PerfilDto {
  administrador: AdministradorDto;
  negocio: NegocioDto;
  administradores: CompaneroDto[];
  hoy: string;
  google_conectado: boolean;
  whatsapp_bot: string | null;
}
