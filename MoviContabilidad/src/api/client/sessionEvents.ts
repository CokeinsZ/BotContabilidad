import type { Sesion } from '../entities';

/**
 * Avisos de la capa api a la sesión:
 * - `refreshed`: se renovó la sesión (trae el perfil actualizado).
 * - `expired`: el servidor rechazó el refresh token (hay que vincular de nuevo).
 */
type RefreshedListener = (sesion: Sesion) => void;
type ExpiredListener = () => void;

const refreshed = new Set<RefreshedListener>();
const expired = new Set<ExpiredListener>();

export function onSessionRefreshed(listener: RefreshedListener): () => void {
  refreshed.add(listener);
  return () => {
    refreshed.delete(listener);
  };
}

export function onSessionExpired(listener: ExpiredListener): () => void {
  expired.add(listener);
  return () => {
    expired.delete(listener);
  };
}

export function emitSessionRefreshed(sesion: Sesion): void {
  refreshed.forEach((listener) => listener(sesion));
}

export function emitSessionExpired(): void {
  expired.forEach((listener) => listener());
}
