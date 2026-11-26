import { useSyncExternalStore } from 'react';

/** El teclado del teléfono tapa al menos esto (en px); menos es la barra del navegador. */
const ALTO_MINIMO_TECLADO = 150;

function suscribir(avisar: () => void): () => void {
  const viewport = window.visualViewport;
  viewport?.addEventListener('resize', avisar);
  return () => viewport?.removeEventListener('resize', avisar);
}

function tecladoAbierto(): boolean {
  const viewport = window.visualViewport;
  return !!viewport && document.documentElement.clientHeight - viewport.height > ALTO_MINIMO_TECLADO;
}

/** Web: true mientras el teclado del teléfono tapa parte de la página. */
export function useKeyboardVisible(): boolean {
  return useSyncExternalStore(suscribir, tecladoAbierto, () => false);
}
