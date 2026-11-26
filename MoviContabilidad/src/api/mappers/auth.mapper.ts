import type { EstadoVinculacionDto, SesionDto, VinculacionDto } from '../dto/auth.dto';
import type { ConsultaVinculacion, Sesion, Vinculacion } from '../entities';
import { toPerfil } from './perfil.mapper';

export function toSesion(dto: SesionDto): Sesion {
  return {
    accessToken: dto.access_token,
    expiraEn: dto.expira_en,
    refreshToken: dto.refresh_token,
    perfil: toPerfil(dto.perfil),
  };
}

/** `ahora` se inyecta para poder probar el vencimiento. */
export function toVinculacion(dto: VinculacionDto, ahora: number = Date.now()): Vinculacion {
  return {
    id: dto.vinculacion_id,
    codigo: dto.codigo,
    mensaje: dto.mensaje,
    whatsappUrl: dto.whatsapp_url,
    venceEn: ahora + dto.expira_en * 1000,
  };
}

export function toConsultaVinculacion(dto: EstadoVinculacionDto): ConsultaVinculacion {
  return { estado: dto.estado, sesion: dto.sesion ? toSesion(dto.sesion) : null };
}
