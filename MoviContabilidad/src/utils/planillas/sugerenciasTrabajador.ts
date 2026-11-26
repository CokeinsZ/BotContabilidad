import { normalizar } from '../text/normalizar';

const NUMERIC = /^[\d$.,]+$/;

/** Parte del texto que es nombre (sin montos): "20.000 mari" -> "mari". */
export function parteNombre(texto: string): string {
  return (texto ?? '')
    .split(/\s+/)
    .filter((token) => token && !NUMERIC.test(token))
    .join(' ');
}

/** Trabajadores cuyo nombre contiene lo que se está escribiendo (sin tildes ni mayúsculas). */
export function sugerirTrabajadores<T extends { nombre: string }>(texto: string, trabajadores: T[], maximo = 5): T[] {
  const consulta = normalizar(parteNombre(texto));
  if (consulta.length < 2) return [];
  return trabajadores
    .filter((trabajador) => {
      const nombre = normalizar(trabajador.nombre);
      return nombre.includes(consulta) && nombre !== consulta;
    })
    .slice(0, maximo);
}

/** Reemplaza la parte del nombre por el elegido, dejando el monto: ("20.000 mari", "maria jose") -> "20.000 maria jose". */
export function completarNombre(texto: string, nombre: string): string {
  const montos = (texto ?? '').split(/\s+/).filter((token) => token && NUMERIC.test(token));
  return [...montos, nombre].join(' ');
}
