/**
 * Alertas de la app (idea de ZoneUp): reemplazo de `Alert.alert` con el estilo
 * de la app. Se dibujan como capa encima de todo, no con <Modal>, así abrir una
 * alerta justo después de cerrar otra no falla. Varias alertas van en cola.
 */
import { createContext, useCallback, useEffect, useMemo, useState, type PropsWithChildren } from 'react';
import { BackHandler, Keyboard, View } from 'react-native';

import type { AlertKind, AlertOptions, Alerts, ConfirmOptions } from './alert.types';
import { AlertDialog } from './AlertDialog';

interface Pending {
  kind: AlertKind;
  title: string;
  message?: string;
  closeText: string;
  confirm?: { text: string; destructive: boolean };
  resolve: (confirmed: boolean) => void;
}

export const AlertContext = createContext<Alerts | null>(null);

export function AlertProvider({ children }: PropsWithChildren) {
  const [queue, setQueue] = useState<Pending[]>([]);
  const current = queue[0] ?? null;

  const push = useCallback((pending: Pending) => {
    Keyboard.dismiss();
    setQueue((items) => [...items, pending]);
  }, []);

  const close = useCallback(
    (confirmed: boolean) => {
      if (!current) return;
      setQueue((items) => items.slice(1));
      current.resolve(confirmed);
    },
    [current],
  );

  useEffect(() => {
    if (!current) return;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      close(false);
      return true;
    });
    return () => subscription.remove();
  }, [current, close]);

  const alerts = useMemo<Alerts>(
    () => ({
      mostrar: (options: AlertOptions) =>
        new Promise<void>((resolve) =>
          push({
            kind: options.tipo ?? 'info',
            title: options.titulo,
            message: options.mensaje,
            closeText: options.textoBoton ?? 'Aceptar',
            resolve: () => resolve(),
          }),
        ),
      confirmar: (options: ConfirmOptions) =>
        new Promise<boolean>((resolve) =>
          push({
            kind: options.destructiva ? 'aviso' : 'pregunta',
            title: options.titulo,
            message: options.mensaje,
            closeText: options.textoCancelar ?? 'Cancelar',
            confirm: { text: options.textoConfirmar ?? 'Confirmar', destructive: !!options.destructiva },
            resolve,
          }),
        ),
    }),
    [push],
  );

  return (
    <AlertContext value={alerts}>
      <View style={{ flex: 1 }}>
        {children}
        {current ? (
          <AlertDialog
            kind={current.kind}
            title={current.title}
            message={current.message}
            closeText={current.closeText}
            confirm={current.confirm}
            onClose={() => close(false)}
            onConfirm={() => close(true)}
          />
        ) : null}
      </View>
    </AlertContext>
  );
}
