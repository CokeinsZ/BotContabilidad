/** Avisos breves ("Enlace copiado", "Guardado"): 2,5 s abajo de la pantalla. */
import { createContext, useCallback, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import { View } from 'react-native';

import { Toast, type ToastTone } from './Toast';

export interface Toasts {
  show: (message: string, tone?: ToastTone) => void;
}

export const ToastContext = createContext<Toasts | null>(null);

const DURATION_MS = 2500;

export function ToastProvider({ children }: PropsWithChildren) {
  const [toast, setToast] = useState<{ id: number; message: string; tone: ToastTone } | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const counter = useRef(0);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const show = useCallback((message: string, tone: ToastTone = 'success') => {
    if (timer.current) clearTimeout(timer.current);
    counter.current += 1;
    setToast({ id: counter.current, message, tone });
    timer.current = setTimeout(() => setToast(null), DURATION_MS);
  }, []);

  const value = useMemo(() => ({ show }), [show]);
  return (
    <ToastContext value={value}>
      <View style={{ flex: 1 }}>
        {children}
        {toast ? <Toast key={toast.id} tone={toast.tone} message={toast.message} /> : null}
      </View>
    </ToastContext>
  );
}
