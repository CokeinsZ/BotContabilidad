import { useEffect, useState } from 'react';

/** La hora actual, actualizada cada `intervaloMs` (cuentas regresivas). */
export function useAhora(intervaloMs = 1000, activo = true): number {
  const [ahora, setAhora] = useState(() => Date.now());
  useEffect(() => {
    if (!activo) return;
    const timer = setInterval(() => setAhora(Date.now()), intervaloMs);
    return () => clearInterval(timer);
  }, [intervaloMs, activo]);
  return ahora;
}
