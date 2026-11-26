import { useQuery } from '@tanstack/react-query';

import { obtenerResumenPlanilla } from '@/api';

import { queryKeys } from '../queryKeys';

export function useResumenPlanilla(planillaId: string) {
  return useQuery({
    queryKey: queryKeys.planillas.resumen(planillaId),
    queryFn: () => obtenerResumenPlanilla(planillaId),
    staleTime: 15_000,
  });
}
