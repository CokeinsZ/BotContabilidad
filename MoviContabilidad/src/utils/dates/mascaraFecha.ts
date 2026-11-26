/**
 * Máscara de `dd-mm-aaaa` mientras se escribe: deja solo dígitos (máximo 8)
 * y pone los guiones. "24112026" -> "24-11-2026"; "2411" -> "24-11".
 */
export function aplicarMascaraFecha(texto: string): string {
  const digits = (texto ?? '').replace(/\D/g, '').slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}-${digits.slice(2)}`;
  return `${digits.slice(0, 2)}-${digits.slice(2, 4)}-${digits.slice(4)}`;
}
