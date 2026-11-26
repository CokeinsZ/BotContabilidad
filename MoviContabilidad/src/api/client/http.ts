/**
 * Peticiones a la API de la app con la sesión.
 *
 * - Adjunta `Authorization: Bearer <access>` (salvo `auth: false`).
 * - Si no hay token de acceso pero sí de refresco (la app recién abrió),
 *   renueva antes de pedir.
 * - Ante un 401 renueva UNA vez y reintenta; si no se puede, la sesión
 *   recibe `expired` y la app vuelve a la pantalla de vinculación.
 */
import { refreshSession } from './refresh';
import { getTokens } from './tokens';
import { parse, send, type SendOptions } from './transport';

export interface RequestOptions extends Omit<SendOptions, 'token'> {
  /** false en /auth/*: no se manda token ni se intenta renovar. */
  auth?: boolean;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, ...sendOptions } = options;
  if (!auth) return parse<T>(await send(path, sendOptions), path);

  if (!getTokens().accessToken && getTokens().refreshToken) {
    await refreshSession();
  }
  let response = await send(path, { ...sendOptions, token: getTokens().accessToken });
  if (response.status === 401 && getTokens().refreshToken) {
    const renewed = await refreshSession();
    if (renewed) response = await send(path, { ...sendOptions, token: getTokens().accessToken });
  }
  return parse<T>(response, path);
}
