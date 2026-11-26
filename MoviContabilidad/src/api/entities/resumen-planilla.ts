import type { Planilla, Totales } from './planilla';

export interface UsoSeccion {
  id: string;
  etiqueta: string;
  usadas: number | null;
  capacidad: number;
}

export interface ResumenPlanilla {
  planilla: Planilla;
  totales: Totales;
  secciones: UsoSeccion[];
}
