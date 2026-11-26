/**
 * Mantiene el splash hasta que la app está lista: fuentes cargadas, sesión
 * restaurada y base de datos local abierta (patrón SplashScreenController de
 * la documentación de Expo Router).
 */
import { useFonts } from 'expo-font';
import { SplashScreen } from 'expo-router';
import { useEffect, useState, type PropsWithChildren } from 'react';

import { useSession } from '@/session';
import { prepararAlmacenamiento } from '@/storage';
import { fontAssets } from '@/theme';

void SplashScreen.preventAutoHideAsync();

export function SplashGate({ children }: PropsWithChildren) {
  const [fontsLoaded, fontError] = useFonts(fontAssets);
  const { estado } = useSession();
  const [almacenamientoListo, setAlmacenamientoListo] = useState(false);

  useEffect(() => {
    void prepararAlmacenamiento().finally(() => setAlmacenamientoListo(true));
  }, []);

  // Si las fuentes fallan se sigue con las del sistema.
  const listo = (fontsLoaded || fontError !== null) && estado !== 'restaurando' && almacenamientoListo;

  useEffect(() => {
    if (listo) SplashScreen.hide();
  }, [listo]);

  return listo ? children : null;
}
