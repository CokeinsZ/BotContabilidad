export const NOMBRES_MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
] as const;

export const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'] as const;

export function capitalizar(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** (2026, 11) -> "Noviembre 2026" */
export function etiquetaMes(anio: number, mes: number): string {
  return `${capitalizar(NOMBRES_MESES[mes - 1] ?? '')} ${anio}`;
}

/** Clave estable de un mes para estados y listas: "2026-11". */
export function claveMes(anio: number, mes: number): string {
  return `${anio}-${String(mes).padStart(2, '0')}`;
}
