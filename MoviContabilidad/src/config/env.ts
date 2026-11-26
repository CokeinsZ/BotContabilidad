/**
 * Variables de entorno públicas (EXPO_PUBLIC_*).
 *
 * Tienen que escribirse con notación de punto (`process.env.EXPO_PUBLIC_X`):
 * Expo las reemplaza por su valor al compilar. Guardarlas en otra variable
 * antes de leerlas haría que no se reemplacen.
 */
function withoutTrailingSlash(url: string): string {
  return url.replace(/\/+$/, '');
}

const rawApiUrl = (process.env.EXPO_PUBLIC_API_URL ?? '').trim();

export const env = {
  /** URL del bot. La API de la app vive en `${apiUrl}/app`. */
  apiUrl: withoutTrailingSlash(rawApiUrl === '' ? 'http://localhost:8000' : rawApiUrl),
} as const;
