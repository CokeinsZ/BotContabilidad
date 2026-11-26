/**
 * Todos los providers de la app, en orden (de afuera hacia adentro).
 * La sesión usa las alertas y la caché, por eso va dentro de ellas.
 */
import { StatusBar } from 'expo-status-bar';
import type { PropsWithChildren } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AlertProvider, ToastProvider } from '@/components/ui/feedback';
import { SessionProvider } from '@/session';

import { QueryProvider } from './QueryProvider';
import { SplashGate } from './SplashGate';

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <QueryProvider>
        <AlertProvider>
          <ToastProvider>
            <SessionProvider>
              <SplashGate>{children}</SplashGate>
            </SessionProvider>
          </ToastProvider>
        </AlertProvider>
      </QueryProvider>
    </SafeAreaProvider>
  );
}
