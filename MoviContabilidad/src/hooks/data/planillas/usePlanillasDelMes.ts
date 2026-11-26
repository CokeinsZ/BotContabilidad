import { useQuery } from '@tanstack/react-query';

import { listarPlanillasDelMes } from '@/api';
import type { MesAnio } from '@/utils/dates/fechaPlanilla';

import { queryKeys } from '../queryKeys';

/** Planillas de un mes. Solo se piden cuando se necesitan (acordeón abierto, calendario visible). */
export function usePlanillasDelMes(mes: MesAnio | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.planillas.delMes(mes?.anio ?? 0, mes?.mes ?? 0),
    queryFn: () => listarPlanillasDelMes(mes!.anio, mes!.mes),
    enabled: enabled && mes !== null,
    staleTime: 30_000,
  });
}
