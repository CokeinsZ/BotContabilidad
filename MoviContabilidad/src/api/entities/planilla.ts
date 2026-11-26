import type { RespuestaBot } from './mensaje';

export interface Planilla {
  id: string;
  /** "24-11-2026-2" */
  nombre: string;
  /** "24-11-2026" */
  fecha: string;
  /** 1 = primera hoja del día. */
  hoja: number;
  url: string;
}

export interface MesPlanillas {
  anio: number;
  mes: number;
  /** "noviembre-2026" (nombre de la carpeta en Drive). */
  carpeta: string;
  /** "Noviembre 2026" */
  etiqueta: string;
}

export interface Totales {
  gastos: number | null;
  efectivo: number | null;
  ventaTotal: number | null;
  saldoPrevio: number | null;
  saldoTotal: number | null;
}

export interface PlanillasDeHoy {
  fecha: string;
  planillas: Planilla[];
  ultima: Planilla | null;
  totales: Totales | null;
}

export interface AperturaPlanilla {
  planilla: Planilla;
  creada: boolean;
  mensajes: RespuestaBot[];
}
