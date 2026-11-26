import { useQuery } from '@tanstack/react-query';

import { obtenerPlanillasDeHoy } from '@/api';

import { queryKeys } from '../queryKeys';

export function usePlanillasDeHoy() {
  return useQuery({ queryKey: queryKeys.planillas.hoy, queryFn: obtenerPlanillasDeHoy, staleTime: 30_000 });
}
