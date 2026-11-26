/**
 * Lo que sobrevive al cerrar la app:
 * - El refresh token, en el llavero seguro del sistema (expo-secure-store).
 * - El último perfil, para poder abrir la app sin red. No es secreto y crece con
 *   la lista de administradores, así que va en el almacén clave-valor de
 *   expo-sqlite: algunas versiones de iOS rechazan valores de más de ~2 KB en el
 *   llavero, y entonces fallaba la vinculación.
 */
import * as SecureStore from 'expo-secure-store';
import Storage from 'expo-sqlite/kv-store';

import type { Perfil } from '@/api';

const REFRESH_KEY = 'movicontabilidad.refresh-token';
const PERFIL_KEY = 'movicontabilidad.perfil';

export interface SesionGuardada {
  refreshToken: string;
  perfil: Perfil | null;
}

export async function leerSesionGuardada(): Promise<SesionGuardada | null> {
  try {
    const refreshToken = await SecureStore.getItemAsync(REFRESH_KEY);
    if (!refreshToken) return null;
    return { refreshToken, perfil: await leerPerfil() };
  } catch {
    return null;
  }
}

async function leerPerfil(): Promise<Perfil | null> {
  try {
    const texto = await Storage.getItem(PERFIL_KEY);
    return texto ? (JSON.parse(texto) as Perfil) : null;
  } catch {
    return null; // Sin perfil guardado se entra igual: el servidor lo manda al renovar la sesión.
  }
}

export async function guardarRefreshToken(refreshToken: string | null): Promise<void> {
  if (refreshToken) {
    await SecureStore.setItemAsync(REFRESH_KEY, refreshToken);
  } else {
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  }
}

/** Caché para abrir sin red: si no se puede guardar, la sesión sigue igual. */
export async function guardarPerfil(perfil: Perfil | null): Promise<void> {
  try {
    if (perfil) {
      await Storage.setItem(PERFIL_KEY, JSON.stringify(perfil));
    } else {
      await Storage.removeItem(PERFIL_KEY);
    }
  } catch {
    // Solo se pierde abrir sin red con el perfil de la última vez.
  }
}

export async function borrarSesionGuardada(): Promise<void> {
  await Promise.all([guardarRefreshToken(null), guardarPerfil(null)]);
}
