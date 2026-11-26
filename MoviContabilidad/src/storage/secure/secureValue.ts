/**
 * Valores secretos (el refresh token): llavero del sistema con expo-secure-store.
 * En la web no hay llavero: ver secureValue.web.ts.
 */
import * as SecureStore from 'expo-secure-store';

export const secureValue = {
  get: (clave: string): Promise<string | null> => SecureStore.getItemAsync(clave),
  set: (clave: string, valor: string): Promise<void> => SecureStore.setItemAsync(clave, valor),
  remove: (clave: string): Promise<void> => SecureStore.deleteItemAsync(clave),
};
