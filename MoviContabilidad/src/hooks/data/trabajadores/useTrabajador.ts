import { useQuery } from '@tanstack/react-query';

import { obtenerTrabajador } from '@/api';

import { queryKeys } from '../queryKeys';

export function useTrabajador(trabajadorId: string) {
  return useQuery({
    queryKey: queryKeys.trabajadores.detalle(trabajadorId),
    queryFn: () => obtenerTrabajador(trabajadorId),
    staleTime: 30_000,
  });
}
