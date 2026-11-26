/**
 * Contexto de sesión: quién está dentro de la app (patrón de ZoneUp) y, además,
 * persistencia: al abrir la app se restaura la sesión guardada; si el servidor
 * la rechaza, se vuelve a la pantalla de vinculación.
 */
import { useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';

import {
  cerrarSesionEnServidor,
  getTokens,
  onSessionExpired,
  onSessionRefreshed,
  onTokensChange,
  refreshSession,
  setTokens,
  type Perfil,
  type Sesion,
} from '@/api';
import { useAlert } from '@/components/ui/feedback';
import { queryKeys } from '@/hooks/data/queryKeys';

import {
  borrarSesionGuardada,
  guardarPerfil,
  guardarRefreshToken,
  leerSesionGuardada,
} from './session.storage';
import type { EstadoSesion, SessionValue } from './session.types';

export const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const alert = useAlert();
  const [estado, setEstado] = useState<EstadoSesion>('restaurando');
  const [perfilGuardado, setPerfilGuardado] = useState<Perfil | null>(null);
  const lastRefreshToken = useRef<string | null>(null);

  const entrar = useCallback(
    (perfil: Perfil) => {
      setPerfilGuardado(perfil);
      queryClient.setQueryData(queryKeys.perfil, perfil);
      setEstado('conSesion');
    },
    [queryClient],
  );

  const salir = useCallback(() => {
    setTokens(null);
    queryClient.clear();
    setPerfilGuardado(null);
    setEstado('sinSesion');
    void borrarSesionGuardada();
  }, [queryClient]);

  // El refresh token rota en cada renovación: se guarda cada vez que cambia.
  useEffect(
    () =>
      onTokensChange(({ refreshToken }) => {
        if (refreshToken === lastRefreshToken.current) return;
        lastRefreshToken.current = refreshToken;
        void guardarRefreshToken(refreshToken);
      }),
    [],
  );

  useEffect(
    () =>
      onSessionRefreshed((sesion) => {
        void guardarPerfil(sesion.perfil);
        setPerfilGuardado(sesion.perfil);
        queryClient.setQueryData(queryKeys.perfil, sesion.perfil);
      }),
    [queryClient],
  );

  useEffect(
    () =>
      onSessionExpired(() => {
        salir();
        void alert.mostrar({
          tipo: 'aviso',
          titulo: 'Tu sesión terminó',
          mensaje: 'Vincula la app de nuevo desde tu WhatsApp para seguir.',
        });
      }),
    [alert, salir],
  );

  // Restaurar la sesión guardada al abrir la app.
  useEffect(() => {
    let activo = true;
    void (async () => {
      const guardada = await leerSesionGuardada();
      if (!activo) return;
      if (!guardada) {
        setEstado('sinSesion');
        return;
      }
      lastRefreshToken.current = guardada.refreshToken;
      setTokens({ accessToken: null, refreshToken: guardada.refreshToken });
      const renovada = await refreshSession();
      if (!activo) return;
      if (renovada) {
        setEstado('conSesion');
      } else if (getTokens().refreshToken) {
        // Sin red: el refresh token sigue guardado. Se entra con el último
        // perfil conocido; las pantallas avisan si no pueden cargar datos.
        if (guardada.perfil) entrar(guardada.perfil);
        else setEstado('conSesion');
      } else {
        salir();
      }
    })();
    return () => {
      activo = false;
    };
  }, [entrar, salir]);

  const value = useMemo<SessionValue>(
    () => ({
      estado,
      administradorId: perfilGuardado?.administrador.id ?? null,
      perfilGuardado,
      completarVinculacion: async (sesion: Sesion) => {
        lastRefreshToken.current = sesion.refreshToken;
        setTokens({ accessToken: sesion.accessToken, refreshToken: sesion.refreshToken });
        await Promise.all([guardarRefreshToken(sesion.refreshToken), guardarPerfil(sesion.perfil)]);
        entrar(sesion.perfil);
      },
      cerrarSesion: async () => {
        const { refreshToken } = getTokens();
        salir();
        if (refreshToken) {
          await cerrarSesionEnServidor(refreshToken).catch(() => undefined);
        }
      },
      recordarPerfil: async (perfil: Perfil) => {
        setPerfilGuardado(perfil);
        queryClient.setQueryData(queryKeys.perfil, perfil);
        await guardarPerfil(perfil);
      },
    }),
    [entrar, estado, perfilGuardado, queryClient, salir],
  );

  return <SessionContext value={value}>{children}</SessionContext>;
}
