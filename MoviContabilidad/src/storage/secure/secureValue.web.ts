/**
 * En la web no existe expo-secure-store: el refresh token queda en `localStorage`.
 * Es lo habitual en una app web sin cookies. La app no carga scripts de terceros,
 * y el token se puede revocar desde WhatsApp ("cerrar app") o con "Cerrar sesión".
 */
export const secureValue = {
  get: async (clave: string): Promise<string | null> => localStorage.getItem(clave),
  set: async (clave: string, valor: string): Promise<void> => localStorage.setItem(clave, valor),
  remove: async (clave: string): Promise<void> => localStorage.removeItem(clave),
};
