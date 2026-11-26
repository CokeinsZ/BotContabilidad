/** GET /app/trabajadores · /app/trabajadores/{id} · /app/trabajadores/{id}/nominas/{hoja_id} */
import { request } from '../client/http';
import type { NominaDetalleDto, TrabajadorDetalleDto, TrabajadoresDto } from '../dto/trabajadores.dto';
import type { DetalleNomina, DetalleTrabajador, ListaTrabajadores } from '../entities';
import { toDetalleNomina, toDetalleTrabajador, toListaTrabajadores } from '../mappers/trabajadores.mapper';

export async function listarTrabajadores(): Promise<ListaTrabajadores> {
  return toListaTrabajadores(await request<TrabajadoresDto>('/trabajadores'));
}

export async function obtenerTrabajador(trabajadorId: string): Promise<DetalleTrabajador> {
  return toDetalleTrabajador(await request<TrabajadorDetalleDto>(`/trabajadores/${encodeURIComponent(trabajadorId)}`));
}

export async function obtenerNomina(trabajadorId: string, hojaId: number): Promise<DetalleNomina> {
  const dto = await request<NominaDetalleDto>(
    `/trabajadores/${encodeURIComponent(trabajadorId)}/nominas/${hojaId}`,
  );
  return toDetalleNomina(dto);
}
