/**
 * Planillas.
 * - GET  /app/planillas/meses                 -> carpetas mes-aaaa (más reciente primero)
 * - GET  /app/planillas?anio=&mes=            -> planillas de un mes
 * - GET  /app/planillas/hoy                   -> planillas de hoy + totales de la última
 * - POST /app/planillas {fecha, hoja}         -> crea o abre (422 si el bot no pudo)
 * - GET  /app/planillas/{id}                  -> detalle
 * - GET  /app/planillas/{id}/resumen          -> totales y filas usadas por sección
 */
import { request } from '../client/http';
import type { AbrirPlanillaDto, HoyDto, MesDto, PlanillaDto, ResumenDto } from '../dto/planillas.dto';
import type { AperturaPlanilla, MesPlanillas, Planilla, PlanillasDeHoy, ResumenPlanilla } from '../entities';
import { toApertura, toMes, toPlanilla, toPlanillasDeHoy, toResumen } from '../mappers/planillas.mapper';

export async function listarMeses(): Promise<MesPlanillas[]> {
  return (await request<MesDto[]>('/planillas/meses')).map(toMes);
}

export async function listarPlanillasDelMes(anio: number, mes: number): Promise<Planilla[]> {
  return (await request<PlanillaDto[]>('/planillas', { query: { anio, mes } })).map(toPlanilla);
}

export async function obtenerPlanillasDeHoy(): Promise<PlanillasDeHoy> {
  return toPlanillasDeHoy(await request<HoyDto>('/planillas/hoy'));
}

export async function crearOAbrirPlanilla(fecha: string, hoja: number): Promise<AperturaPlanilla> {
  return toApertura(await request<AbrirPlanillaDto>('/planillas', { method: 'POST', body: { fecha, hoja } }));
}

export async function obtenerPlanilla(planillaId: string): Promise<Planilla> {
  return toPlanilla(await request<PlanillaDto>(`/planillas/${encodeURIComponent(planillaId)}`));
}

export async function obtenerResumenPlanilla(planillaId: string): Promise<ResumenPlanilla> {
  return toResumen(await request<ResumenDto>(`/planillas/${encodeURIComponent(planillaId)}/resumen`));
}
