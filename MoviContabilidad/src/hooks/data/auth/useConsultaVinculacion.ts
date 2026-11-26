import { useQuery } from '@tanstack/react-query';

import { consultarVinculacion } from '@/api';
import { APP } from '@/constants/app';

import { queryKeys } from '../queryKeys';

/** Pregunta cada 2 s si el bot ya confirmó la vinculación (y al volver de WhatsApp). */
export function useConsultaVinculacion(vinculacionId: string | null, activa: boolean) {
  return useQuery({
    queryKey: queryKeys.vinculacion(vinculacionId ?? 'ninguna'),
    queryFn: () => consultarVinculacion(vinculacionId!),
    enabled: !!vinculacionId && activa,
    refetchInterval: activa ? APP.pairingPollMs : false,
    refetchOnWindowFocus: 'always',
    gcTime: 0,
    staleTime: 0,
  });
}
