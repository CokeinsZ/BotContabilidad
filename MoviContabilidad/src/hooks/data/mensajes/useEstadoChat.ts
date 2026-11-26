import { useQuery } from '@tanstack/react-query';

import { obtenerEstadoChat } from '@/api';

import { queryKeys } from '../queryKeys';

/** Pregunta pendiente del bot y qué revertiría "Deshacer". */
export function useEstadoChat(planillaId: string) {
  return useQuery({
    queryKey: queryKeys.chat.estado(planillaId),
    queryFn: () => obtenerEstadoChat(planillaId),
    staleTime: 0,
  });
}
