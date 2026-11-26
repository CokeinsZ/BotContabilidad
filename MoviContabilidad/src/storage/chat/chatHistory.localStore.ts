/**
 * Historial del chat en la web: las mismas filas de la tabla `mensajes` de
 * SQLite, guardadas como JSON en `localStorage`. Solo lo importan los archivos
 * `.web.ts`. Con 90 días de historial son unos cientos de KB.
 */
import type { FilaMensaje } from './chatHistory.types';

const CLAVE = 'movicontabilidad.mensajes';

export interface AlmacenMensajes {
  siguienteId: number;
  filas: FilaMensaje[];
}

export function leerAlmacen(): AlmacenMensajes {
  try {
    const texto = localStorage.getItem(CLAVE);
    if (texto) return JSON.parse(texto) as AlmacenMensajes;
  } catch {
    // Dañado o sin acceso: se empieza vacío.
  }
  return { siguienteId: 1, filas: [] };
}

/** Lee, aplica el cambio y guarda. */
export function modificarAlmacen(cambio: (almacen: AlmacenMensajes) => void): void {
  const almacen = leerAlmacen();
  cambio(almacen);
  localStorage.setItem(CLAVE, JSON.stringify(almacen));
}
