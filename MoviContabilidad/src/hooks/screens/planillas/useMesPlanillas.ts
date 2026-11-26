import type { MesPlanillas } from '@/api';
import { errorMessage } from '@/api';
import { usePlanillasDelMes } from '@/hooks/data/planillas/usePlanillasDelMes';

/** Planillas de un mes del acordeón: solo se piden cuando el mes está abierto. */
export function useMesPlanillas(mes: MesPlanillas, abierto: boolean) {
  const query = usePlanillasDelMes({ anio: mes.anio, mes: mes.mes }, abierto);
  const cantidad = query.data?.length;
  return {
    planillas: query.data ?? [],
    cargando: query.isLoading,
    error: query.error ? errorMessage(query.error) : null,
    reintentar: () => void query.refetch(),
    subtitulo: cantidad === undefined ? 'Toca para ver' : cantidad === 1 ? '1 planilla' : `${cantidad} planillas`,
  };
}
