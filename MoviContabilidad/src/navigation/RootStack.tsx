/**
 * Stack raíz (idea de ZoneUp + documentación de Expo Router): sin sesión,
 * las pantallas de la app no existen. Al vincular o al cerrar sesión no se
 * navega a mano: cambia la sesión y `Stack.Protected` redirige solo.
 */
import { Stack } from 'expo-router';

import { useSession } from '@/session';

import { routes } from './routes';
import { rootStackOptions } from './stackOptions';

export function RootStack() {
  const { estado } = useSession();
  const conSesion = estado === 'conSesion';
  return (
    <Stack screenOptions={rootStackOptions}>
      <Stack.Protected guard={conSesion} redirectTo={routes.vincular}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
      <Stack.Protected guard={!conSesion} redirectTo={routes.principal}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}
