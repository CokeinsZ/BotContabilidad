const PALABRAS_VACIAS = new Set(['de', 'del', 'la', 'las', 'el', 'los', 'y', 'e']);

/** "Panadería La Espiga" -> "PE"; "juan" -> "J". Para avatares y monogramas. */
export function iniciales(nombre: string, maximo = 2): string {
  const words = (nombre ?? '').trim().split(/\s+/).filter(Boolean);
  const significant = words.filter((word) => !PALABRAS_VACIAS.has(word.toLowerCase()));
  const source = significant.length > 0 ? significant : words;
  return source
    .slice(0, maximo)
    .map((word) => word.charAt(0).toUpperCase())
    .join('');
}
