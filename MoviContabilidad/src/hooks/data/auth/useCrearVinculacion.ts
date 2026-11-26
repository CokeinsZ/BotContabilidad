import { useMutation } from '@tanstack/react-query';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

import { crearVinculacion } from '@/api';

/** Nombre del teléfono para el mensaje del bot ("App vinculada en iPhone de Marta"). */
function nombreDelDispositivo(): string | null {
  // En la web no hay nombre del teléfono, y el modelo del navegador no es fiable.
  if (Platform.OS === 'web') return Device.osName ? `navegador (${Device.osName})` : 'navegador';
  return Device.deviceName ?? Device.modelName ?? null;
}

export function useCrearVinculacion() {
  return useMutation({ mutationFn: () => crearVinculacion(nombreDelDispositivo()) });
}
