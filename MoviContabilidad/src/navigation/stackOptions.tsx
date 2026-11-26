import type { NativeStackNavigationOptions } from 'expo-router';

import { AppHeader } from '@/components/navigation';
import { colors } from '@/theme';

const content = { backgroundColor: colors.background.screen };

/** Stack raíz: solo agrupa (app) y (auth); cada grupo pone su encabezado. */
export const rootStackOptions: NativeStackNavigationOptions = {
  headerShown: false,
  contentStyle: content,
};

/** Pantallas de la app: encabezado propio con filete dorado (AppHeader). */
export const appStackOptions: NativeStackNavigationOptions = {
  header: (props) => <AppHeader {...props} />,
  // iOS 26+ deja el encabezado transparente por defecto: aquí no.
  headerTransparent: false,
  contentStyle: content,
};

export const authStackOptions: NativeStackNavigationOptions = {
  headerShown: false,
  contentStyle: content,
};
