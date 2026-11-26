import { useQuery } from '@tanstack/react-query';

import { obtenerNomina } from '@/api';

import { queryKeys } from '../queryKeys';

export function useNominaArchivada(trabajadorId: string, hojaId: number) {
  return useQuery({
    queryKey: queryKeys.trabajadores.nomina(trabajadorId, hojaId),
    queryFn: () => obtenerNomina(trabajadorId, hojaId),
    staleTime: Infinity,
    enabled: Number.isInteger(hojaId),
  });
}
