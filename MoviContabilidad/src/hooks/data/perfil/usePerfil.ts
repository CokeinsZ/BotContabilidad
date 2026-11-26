import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { obtenerPerfil } from '@/api';
import { useSession } from '@/session';

import { queryKeys } from '../queryKeys';

/** Perfil del administrador y su negocio. Arranca con el último guardado (sirve sin red). */
export function usePerfil() {
  const { perfilGuardado, recordarPerfil } = useSession();
  const query = useQuery({
    queryKey: queryKeys.perfil,
    queryFn: obtenerPerfil,
    initialData: perfilGuardado ?? undefined,
    initialDataUpdatedAt: 0,
    staleTime: 5 * 60_000,
  });
  useEffect(() => {
    if (query.data && query.data !== perfilGuardado) void recordarPerfil(query.data);
  }, [query.data, perfilGuardado, recordarPerfil]);
  return query;
}
