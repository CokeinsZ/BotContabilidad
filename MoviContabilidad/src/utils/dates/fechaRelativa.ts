import { compararFechas, formatFecha, parseFecha } from './fechaPlanilla';
import { MESES_CORTOS, NOMBRES_MESES, capitalizar } from './meses';

const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'] as const;
const DIAS_CORTOS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'] as const;

/** "24-11-2026" -> "Mar 24 nov" (filas de planillas). */
export function diaCorto(texto: string): string {
  const date = parseFecha(texto);
  if (!date) return texto;
  return `${capitalizar(DIAS_CORTOS[date.getDay()])} ${date.getDate()} ${MESES_CORTOS[date.getMonth()]}`;
}

/** "24-11-2026" -> "martes 24 de noviembre" (saludo de la pantalla Principal). */
export function fechaLarga(texto: string): string {
  const date = parseFecha(texto);
  if (!date) return texto;
  return `${DIAS[date.getDay()]} ${date.getDate()} de ${NOMBRES_MESES[date.getMonth()]}`;
}

/** Separador de días del chat: "Hoy", "Ayer" o "lun 23 nov". */
export function etiquetaDia(instante: number, hoy: string): string {
  const fecha = formatFecha(new Date(instante));
  const diferencia = compararFechas(hoy, fecha);
  if (diferencia === 0) return 'Hoy';
  if (diferencia === 1) return 'Ayer';
  const date = new Date(instante);
  return `${DIAS_CORTOS[date.getDay()]} ${date.getDate()} ${MESES_CORTOS[date.getMonth()]}`;
}

/** Hora corta del chat: "9:05 a. m." */
export function horaCorta(instante: number): string {
  const date = new Date(instante);
  const hours = date.getHours();
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const suffix = hours < 12 ? 'a. m.' : 'p. m.';
  const hour12 = hours % 12 === 0 ? 12 : hours % 12;
  return `${hour12}:${minutes} ${suffix}`;
}
