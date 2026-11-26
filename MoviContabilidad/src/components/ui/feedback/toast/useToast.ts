import { use } from 'react';

import { ToastContext, type Toasts } from './ToastProvider';

export function useToast(): Toasts {
  const value = use(ToastContext);
  if (!value) throw new Error('useToast debe usarse dentro de <ToastProvider />');
  return value;
}
