/**
 * Tokens de la sesión.
 *
 * El de acceso vive solo en memoria. El de refresco también, y la sesión lo
 * guarda en `expo-secure-store` escuchando `onTokensChange` (la capa api no
 * conoce el almacenamiento).
 */
export interface Tokens {
  accessToken: string | null;
  refreshToken: string | null;
}

type Listener = (tokens: Tokens) => void;

let current: Tokens = { accessToken: null, refreshToken: null };
const listeners = new Set<Listener>();

export function getTokens(): Tokens {
  return current;
}

/** Reemplaza los tokens. `null` borra los dos (cerrar sesión). */
export function setTokens(next: Partial<Tokens> | null): void {
  current = next === null ? { accessToken: null, refreshToken: null } : { ...current, ...next };
  listeners.forEach((listener) => listener(current));
}

export function onTokensChange(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
