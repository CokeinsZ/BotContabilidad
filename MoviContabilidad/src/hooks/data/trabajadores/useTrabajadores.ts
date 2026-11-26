import { useQuery } from '@tanstack/react-query';

import { listarTrabajadores } from '@/api';

import { queryKeys } from '../queryKeys';

export function useTrabajadores(enabled = true) {
  return useQuery({ queryKey: queryKeys.trabajadores.lista, queryFn: listarTrabajadores, staleTime: 60_000, enabled });
}
