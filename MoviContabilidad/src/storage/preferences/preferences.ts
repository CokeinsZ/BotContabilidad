/**
 * Preferencias pequeñas del teléfono (p. ej. "ya vi la pista del doble toque").
 * Usa el almacén clave-valor de expo-sqlite (reemplazo de AsyncStorage).
 */
import Storage from 'expo-sqlite/kv-store';

export const PREFERENCIAS = {
  pistaDobleToqueVista: 'pista-doble-toque-vista',
} as const;

type Clave = (typeof PREFERENCIAS)[keyof typeof PREFERENCIAS];

export async function leerPreferencia(clave: Clave): Promise<string | null> {
  try {
    return await Storage.getItem(clave);
  } catch {
    return null;
  }
}

export async function guardarPreferencia(clave: Clave, valor: string): Promise<void> {
  try {
    await Storage.setItem(clave, valor);
  } catch {
    // Una preferencia que no se guarda no debe romper la pantalla.
  }
}
