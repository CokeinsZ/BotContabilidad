/**
 * Fechas de planilla: texto `dd-mm-aaaa` (el mismo formato del bot y de los
 * nombres de archivo en Drive) ⇄ `Date`.
 *
 * Las fechas se crean a las 12:00 locales para que ningún cambio de horario
 * mueva el día.
 */
const PATTERN = /^(\d{2})-(\d{2})-(\d{4})$/;

export function parseFecha(texto: string): Date | null {
  const match = PATTERN.exec((texto ?? '').trim());
  if (!match) return null;
  const [, dd, mm, yyyy] = match;
  const day = Number(dd);
  const month = Number(mm);
  const year = Number(yyyy);
  const date = new Date(year, month - 1, day, 12);
  const sameDay = date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  return sameDay ? date : null;
}

export function esFechaValida(texto: string): boolean {
  return parseFecha(texto) !== null;
}

export function formatFecha(date: Date): string {
  const dd = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  return `${dd}-${mm}-${date.getFullYear()}`;
}

export function sumarDias(texto: string, dias: number): string | null {
  const date = parseFecha(texto);
  if (!date) return null;
  date.setDate(date.getDate() + dias);
  return formatFecha(date);
}

/** Negativo si `a` es antes que `b`, 0 si es el mismo día, positivo si es después. */
export function compararFechas(a: string, b: string): number {
  const first = parseFecha(a);
  const second = parseFecha(b);
  if (!first || !second) return 0;
  return Math.round((first.getTime() - second.getTime()) / 86_400_000);
}

export interface MesAnio {
  anio: number;
  /** 1 = enero. */
  mes: number;
}

export function mesDe(texto: string): MesAnio | null {
  const date = parseFecha(texto);
  return date ? { anio: date.getFullYear(), mes: date.getMonth() + 1 } : null;
}

export function mesAnterior({ anio, mes }: MesAnio): MesAnio {
  return mes === 1 ? { anio: anio - 1, mes: 12 } : { anio, mes: mes - 1 };
}

export function mesSiguiente({ anio, mes }: MesAnio): MesAnio {
  return mes === 12 ? { anio: anio + 1, mes: 1 } : { anio, mes: mes + 1 };
}

export function mismoMes(a: MesAnio | null, b: MesAnio | null): boolean {
  return !!a && !!b && a.anio === b.anio && a.mes === b.mes;
}
