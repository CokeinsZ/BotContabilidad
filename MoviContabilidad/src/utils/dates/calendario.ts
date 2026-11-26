import { formatFecha, type MesAnio } from './fechaPlanilla';

export interface DiaCalendario {
  /** dd-mm-aaaa */
  fecha: string;
  dia: number;
  delMes: boolean;
}

/**
 * Las 6 semanas (de lunes a domingo) que muestran un mes completo, con los
 * días del mes anterior y del siguiente para llenar los huecos.
 */
export function semanasDelMes({ anio, mes }: MesAnio): DiaCalendario[][] {
  const first = new Date(anio, mes - 1, 1, 12);
  // getDay(): 0 = domingo. Las semanas empiezan en lunes.
  const offset = (first.getDay() + 6) % 7;
  const start = new Date(anio, mes - 1, 1 - offset, 12);
  const weeks: DiaCalendario[][] = [];
  for (let week = 0; week < 6; week += 1) {
    const days: DiaCalendario[] = [];
    for (let weekday = 0; weekday < 7; weekday += 1) {
      const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + week * 7 + weekday, 12);
      days.push({ fecha: formatFecha(date), dia: date.getDate(), delMes: date.getMonth() === mes - 1 });
    }
    weeks.push(days);
  }
  return weeks;
}

export const DIAS_SEMANA_CORTOS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'] as const;
