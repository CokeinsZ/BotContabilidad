/** "  Panadería   La Espiga " -> "Panadería La Espiga": así lo guarda el bot. */
export function limpiarNombre(texto: string): string {
  return texto.trim().replace(/\s+/g, ' ');
}
