/**
 * Vinculación y sesión (públicos: no llevan token).
 * - POST /app/auth/vinculaciones          -> código para enviar al bot por WhatsApp
 * - GET  /app/auth/vinculaciones/{id}     -> pendiente | confirmada (+sesión, una vez) | consumida | expirada
 * - POST /app/auth/logout                 -> 204 (siempre)
 * El refresh vive en client/refresh.ts (lo usa http.ts ante un 401).
 */
import { request } from '../client/http';
import type { EstadoVinculacionDto, VinculacionDto } from '../dto/auth.dto';
import type { ConsultaVinculacion, Vinculacion } from '../entities';
import { toConsultaVinculacion, toVinculacion } from '../mappers/auth.mapper';

export async function crearVinculacion(dispositivo: string | null): Promise<Vinculacion> {
  const dto = await request<VinculacionDto>('/auth/vinculaciones', {
    method: 'POST',
    body: { dispositivo },
    auth: false,
  });
  return toVinculacion(dto);
}

export async function consultarVinculacion(vinculacionId: string): Promise<ConsultaVinculacion> {
  const dto = await request<EstadoVinculacionDto>(`/auth/vinculaciones/${encodeURIComponent(vinculacionId)}`, {
    auth: false,
  });
  return toConsultaVinculacion(dto);
}

export async function cerrarSesionEnServidor(refreshToken: string): Promise<void> {
  await request<void>('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken }, auth: false });
}
