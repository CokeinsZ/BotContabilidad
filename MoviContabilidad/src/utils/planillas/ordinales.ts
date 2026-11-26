const ORDINALES = ['Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta', 'Sexta', 'Séptima', 'Octava', 'Novena', 'Décima'];

/** 1 -> "Primera", 2 -> "Segunda"… (después de la décima: "Hoja 11"). */
export function nombreOrdinal(hoja: number): string {
  return ORDINALES[hoja - 1] ?? `Hoja ${hoja}`;
}

/** Nombre del archivo en Drive: ("24-11-2026", 1) -> "24-11-2026"; (…, 2) -> "24-11-2026-2". */
export function nombrePlanilla(fecha: string, hoja: number): string {
  return hoja === 1 ? fecha : `${fecha}-${hoja}`;
}

/** "24-11-2026 · Hoja 2" */
export function tituloPlanilla(fecha: string, hoja: number): string {
  return `${fecha} · Hoja ${hoja}`;
}
