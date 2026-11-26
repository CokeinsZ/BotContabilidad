/**
 * Clave de comparación sin mayúsculas, tildes, diéresis ni ñ, con espacios
 * simples. Es la misma regla de `name_key` del bot: "MUÑOZ  Pérez" -> "munoz perez".
 */
export function normalizar(texto: string): string {
  return (texto ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .join(' ');
}

export function contiene(texto: string, busqueda: string): boolean {
  return normalizar(texto).includes(normalizar(busqueda));
}
