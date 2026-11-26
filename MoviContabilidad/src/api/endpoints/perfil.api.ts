/** GET /app/perfil · PATCH /app/negocio · PATCH /app/administrador */
import { request } from '../client/http';
import type { PerfilDto } from '../dto/perfil.dto';
import type { Perfil } from '../entities';
import { toPerfil } from '../mappers/perfil.mapper';

export async function obtenerPerfil(): Promise<Perfil> {
  return toPerfil(await request<PerfilDto>('/perfil'));
}

export async function actualizarNegocio(nombre: string): Promise<Perfil> {
  return toPerfil(await request<PerfilDto>('/negocio', { method: 'PATCH', body: { nombre } }));
}

export async function actualizarAdministrador(nombre: string): Promise<Perfil> {
  return toPerfil(await request<PerfilDto>('/administrador', { method: 'PATCH', body: { nombre } }));
}
