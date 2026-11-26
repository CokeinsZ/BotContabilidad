/**
 * React Query: caché, reintentos y recarga al volver a la app.
 * En React Native el "foco" es el AppState (activo / en segundo plano).
 */
import { QueryClient, QueryClientProvider, focusManager } from '@tanstack/react-query';
import { useEffect, useState, type PropsWithChildren } from 'react';
import { AppState, type AppStateStatus } from 'react-native';

import { isRetryable } from '@/api';

function onAppStateChange(status: AppStateStatus) {
  focusManager.setFocused(status === 'active');
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Sin red o servidor caído: hasta dos reintentos. Un 4xx no se reintenta.
        retry: (failureCount, error) => failureCount < 2 && isRetryable(error),
        staleTime: 30_000,
        refetchOnWindowFocus: true,
      },
      mutations: { retry: false },
    },
  });
}

export function QueryProvider({ children }: PropsWithChildren) {
  const [client] = useState(createQueryClient);
  useEffect(() => {
    const subscription = AppState.addEventListener('change', onAppStateChange);
    return () => subscription.remove();
  }, []);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
