import { useInfiniteQuery } from '@tanstack/react-query';

import type { Mensaje } from '@/api';
import { APP } from '@/constants/app';
import { useSession } from '@/session';
import { listarMensajes } from '@/storage';

import { queryKeys } from '../queryKeys';

/** Historial del chat de una planilla, leído del SQLite del teléfono (del más nuevo al más viejo). */
export function useHistorialChat(planillaId: string) {
  const { administradorId } = useSession();
  const query = useInfiniteQuery({
    queryKey: queryKeys.chat.historial(administradorId ?? 0, planillaId),
    queryFn: ({ pageParam }) =>
      listarMensajes(administradorId ?? 0, planillaId, { antesDe: pageParam, limite: APP.chatPageSize }),
    initialPageParam: undefined as number | undefined,
    getNextPageParam: (lastPage: Mensaje[]) =>
      lastPage.length === APP.chatPageSize ? lastPage[lastPage.length - 1].id : undefined,
    enabled: administradorId !== null,
    staleTime: Infinity,
    networkMode: 'always',
  });
  const mensajes = query.data?.pages.flat() ?? [];
  return { ...query, mensajes };
}
