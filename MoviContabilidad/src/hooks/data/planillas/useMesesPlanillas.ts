import { useQuery } from '@tanstack/react-query';

import { listarMeses } from '@/api';

import { queryKeys } from '../queryKeys';

export function useMesesPlanillas() {
  return useQuery({ queryKey: queryKeys.planillas.meses, queryFn: listarMeses, staleTime: 60_000 });
}
