/**
 * Versión web del almacén clave-valor: `localStorage` del navegador.
 * (expo-sqlite en la web exige cabeceras COOP/COEP que Safari no soporta del todo.)
 */
export const kv = {
  getItem: async (clave: string): Promise<string | null> => localStorage.getItem(clave),
  setItem: async (clave: string, valor: string): Promise<void> => localStorage.setItem(clave, valor),
  removeItem: async (clave: string): Promise<void> => localStorage.removeItem(clave),
};
