/**
 * Almacén clave-valor pequeño del teléfono (preferencias, perfil en caché).
 * En el teléfono usa el de expo-sqlite; en la web, `localStorage` (kv.web.ts).
 */
import Storage from 'expo-sqlite/kv-store';

export const kv = {
  getItem: (clave: string): Promise<string | null> => Storage.getItem(clave),
  setItem: (clave: string, valor: string): Promise<void> => Storage.setItem(clave, valor),
  removeItem: (clave: string): Promise<void> => Storage.removeItem(clave),
};
