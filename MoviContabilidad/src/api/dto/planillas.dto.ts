import type { RespuestaDto } from './mensajes.dto';

export interface MesDto {
  anio: number;
  mes: number;
  carpeta: string;
  etiqueta: string;
}

export interface PlanillaDto {
  id: string;
  nombre: string;
  fecha: string;
  hoja: number;
  url: string;
}

export interface TotalesDto {
  gastos: number | null;
  efectivo: number | null;
  venta_total: number | null;
  saldo_previo: number | null;
  saldo_total: number | null;
}

export interface HoyDto {
  fecha: string;
  planillas: PlanillaDto[];
  ultima: PlanillaDto | null;
  totales: TotalesDto | null;
}

export interface SeccionDto {
  id: string;
  etiqueta: string;
  usadas: number | null;
  capacidad: number;
}

export interface ResumenDto {
  planilla: PlanillaDto;
  totales: TotalesDto;
  secciones: SeccionDto[];
}

export interface AbrirPlanillaDto {
  planilla: PlanillaDto;
  creada: boolean;
  mensajes: RespuestaDto[];
}
