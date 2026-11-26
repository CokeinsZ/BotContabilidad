import { use } from 'react';

import { SessionContext } from './SessionProvider';
import type { SessionValue } from './session.types';

/** `const { estado, cerrarSesion } = useSession()` desde cualquier pantalla o hook. */
export function useSession(): SessionValue {
  const value = use(SessionContext);
  if (!value) throw new Error('useSession debe usarse dentro de <SessionProvider />');
  return value;
}
