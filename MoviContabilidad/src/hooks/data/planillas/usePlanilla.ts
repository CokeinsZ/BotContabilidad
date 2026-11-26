import { useQuery, useQueryClient } from '@tanstack/react-query';

import { obtenerPlanilla, type Planilla } from '@/api';

import { queryKeys } from '../queryKeys';

/** Detalle de una planilla. Si ya está en algún listado, se muestra al instante. */
export function usePlanilla(planillaId: string) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: queryKeys.planillas.detalle(planillaId),
    queryFn: () => obtenerPlanilla(planillaId),
    staleTime: Infinity,
    initialData: () => {
      for (const [, data] of queryClient.getQueriesData<Planilla[]>({ queryKey: queryKeys.planillas.mesesYMeses })) {
        const found = data?.find((planilla) => planilla.id === planillaId);
        if (found) return found;
      }
      return undefined;
    },
  });
}
