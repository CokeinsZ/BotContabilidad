import { nombreOrdinal } from './ordinales';

/** Lo mínimo de una planilla que necesitan estas reglas. */
export interface PlanillaBasica {
  id: string;
  nombre: string;
  fecha: string;
  hoja: number;
}

export interface OpcionHoja {
  hoja: number;
  etiqueta: string;
  /** Ya existe: la acción es abrirla. */
  existe: boolean;
  /** Se puede abrir o crear ahora (las hojas se crean en orden). */
  disponible: boolean;
  descripcion?: string;
  planillaId?: string;
}

function hojasDelDia(fecha: string, planillas: PlanillaBasica[]): PlanillaBasica[] {
  return planillas.filter((planilla) => planilla.fecha === fecha).sort((a, b) => a.hoja - b.hoja);
}

/** La hoja que se crearía ahora en esa fecha (la siguiente a la última que existe). */
export function siguienteHoja(fecha: string, planillas: PlanillaBasica[]): number {
  const existentes = hojasDelDia(fecha, planillas);
  return (existentes.at(-1)?.hoja ?? 0) + 1;
}

/**
 * Opciones del selector de hoja para una fecha: Primera, Segunda, Tercera
 * siempre (mínimo `minimo`) y una más si ya existen todas. Las que existen se
 * abren; solo se puede crear la siguiente a la última, como hace el bot.
 */
export function opcionesHojas(fecha: string, planillas: PlanillaBasica[], minimo = 3): OpcionHoja[] {
  const existentes = hojasDelDia(fecha, planillas);
  const porHoja = new Map(existentes.map((planilla) => [planilla.hoja, planilla]));
  const siguiente = siguienteHoja(fecha, planillas);
  const total = Math.max(minimo, siguiente);
  const opciones: OpcionHoja[] = [];
  for (let hoja = 1; hoja <= total; hoja += 1) {
    const planilla = porHoja.get(hoja);
    const existe = planilla !== undefined;
    const disponible = existe || hoja === siguiente;
    opciones.push({
      hoja,
      etiqueta: nombreOrdinal(hoja),
      existe,
      disponible,
      planillaId: planilla?.id,
      descripcion: existe
        ? 'Ya existe: se abrirá'
        : disponible
          ? undefined
          : `Crea primero la ${nombreOrdinal(hoja - 1).toLowerCase()}`,
    });
  }
  return opciones;
}

/**
 * De dónde sale el saldo de caja (B42) de una planilla nueva, con las reglas
 * del bot: la hoja N toma el saldo total de la N-1 del mismo día; la primera
 * del día, el de la hoja más alta del día anterior. null si no hay de dónde.
 */
export function origenSaldo(
  fecha: string,
  hoja: number,
  planillas: PlanillaBasica[],
  fechaAnterior: string | null,
): PlanillaBasica | null {
  if (hoja > 1) {
    return hojasDelDia(fecha, planillas).find((planilla) => planilla.hoja === hoja - 1) ?? null;
  }
  if (!fechaAnterior) return null;
  return hojasDelDia(fechaAnterior, planillas).at(-1) ?? null;
}
