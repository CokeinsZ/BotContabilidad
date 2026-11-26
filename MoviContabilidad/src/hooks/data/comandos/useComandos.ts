import { useQuery } from '@tanstack/react-query';

import { listarComandos } from '@/api';
import { COMANDOS_RESPALDO } from '@/constants/comandosRespaldo';

import { queryKeys } from '../queryKeys';

/** Catálogo de la banda. Si el bot no responde, se usa el catálogo local. */
export function useComandos() {
  const query = useQuery({
    queryKey: queryKeys.comandos,
    queryFn: listarComandos,
    staleTime: Infinity,
    placeholderData: COMANDOS_RESPALDO,
  });
  return { ...query, comandos: query.data ?? COMANDOS_RESPALDO };
}
