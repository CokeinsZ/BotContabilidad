/**
 * Preferencias pequeñas del teléfono (p. ej. "ya vi la pista del doble toque").
 * Usa el almacén clave-valor local (expo-sqlite en el teléfono, localStorage en la web).
 */
import { kv } from '../kv/kv';

export const PREFERENCIAS = {
  pistaDobleToqueVista: 'pista-doble-toque-vista',
} as const;

type Clave = (typeof PREFERENCIAS)[keyof typeof PREFERENCIAS];

export async function leerPreferencia(clave: Clave): Promise<string | null> {
  try {
    return await kv.getItem(clave);
  } catch {
    return null;
  }
}

export async function guardarPreferencia(clave: Clave, valor: string): Promise<void> {
  try {
    await kv.setItem(clave, valor);
  } catch {
    // Una preferencia que no se guarda no debe romper la pantalla.
  }
}
