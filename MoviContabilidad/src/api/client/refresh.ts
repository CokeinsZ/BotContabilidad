/**
 * Renovación de la sesión ante un 401.
 *
 * "Single-flight": si cinco peticiones reciben 401 a la vez, se hace UN solo
 * refresh y las cinco esperan ese mismo resultado. El refresh token rota en
 * cada uso, así que dos refresh simultáneos dejarían la sesión inválida.
 */
import type { SesionDto } from '../dto/auth.dto';
import { toSesion } from '../mappers/auth.mapper';
import { ApiError } from './errors';
import { emitSessionExpired, emitSessionRefreshed } from './sessionEvents';
import { getTokens, setTokens } from './tokens';
import { parse, send } from './transport';

let inFlight: Promise<boolean> | null = null;

/** true si la sesión quedó renovada. false si no hay red (los tokens se conservan) o si expiró. */
export function refreshSession(): Promise<boolean> {
  inFlight ??= doRefresh().finally(() => {
    inFlight = null;
  });
  return inFlight;
}

async function doRefresh(): Promise<boolean> {
  const { refreshToken } = getTokens();
  if (!refreshToken) return false;
  try {
    const response = await send('/auth/refresh', { method: 'POST', body: { refresh_token: refreshToken } });
    const sesion = toSesion(await parse<SesionDto>(response, '/auth/refresh'));
    setTokens({ accessToken: sesion.accessToken, refreshToken: sesion.refreshToken });
    emitSessionRefreshed(sesion);
    return true;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      setTokens(null);
      emitSessionExpired();
    }
    return false;
  }
}
