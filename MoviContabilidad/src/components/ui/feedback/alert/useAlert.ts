import { use } from 'react';

import type { Alerts } from './alert.types';
import { AlertContext } from './AlertProvider';

export function useAlert(): Alerts {
  const value = use(AlertContext);
  if (!value) throw new Error('useAlert debe usarse dentro de <AlertProvider />');
  return value;
}
