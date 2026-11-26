/**
 * Web: la app ocupa exactamente la parte visible de la pantalla.
 *
 * En el navegador del teléfono el teclado no achica la página: tapa la parte de
 * abajo (solo se achica el "visual viewport") y Safari además desplaza la página
 * hacia arriba para mostrar el campo. La raíz es `position: fixed` (ver
 * public/index.html): aquí se le da el alto visible y se mueve con el desplazamiento.
 * Así el encabezado no se va y la banda de comandos queda encima del teclado.
 */
import { useEffect } from 'react';

export function VisualViewportRoot() {
  useEffect(() => {
    const viewport = window.visualViewport;
    const root = document.getElementById('root');
    if (!viewport || !root) return undefined;
    const ajustar = () => {
      root.style.height = `${viewport.height}px`;
      root.style.transform = `translateY(${viewport.offsetTop}px)`;
    };
    ajustar();
    viewport.addEventListener('resize', ajustar);
    viewport.addEventListener('scroll', ajustar);
    return () => {
      viewport.removeEventListener('resize', ajustar);
      viewport.removeEventListener('scroll', ajustar);
    };
  }, []);
  return null;
}
