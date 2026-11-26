import type { MesAnio } from '@/utils/dates/fechaPlanilla';

export interface CalendarProps {
  /** Mes que se está mostrando. */
  month: MesAnio;
  onMonthChange: (month: MesAnio) => void;
  /** Día seleccionado (dd-mm-aaaa). */
  selected: string | null;
  onSelect: (fecha: string) => void;
  /** Hoy (dd-mm-aaaa): se marca con un aro dorado. */
  today: string;
  /** Puntos bajo cada día (dd-mm-aaaa -> cantidad, máximo 3 visibles). */
  marks?: Record<string, number>;
}
