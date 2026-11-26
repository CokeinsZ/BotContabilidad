/**
 * Montos como los escribe el bot: 5000 -> "$5.000"; 2500.5 -> "$2.500,50";
 * -3000 -> "-$3.000". null -> "—".
 */
export function formatearMonto(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—';
  const sign = valor < 0 ? '-' : '';
  const absolute = Math.abs(valor);
  const entero = Number.isInteger(absolute);
  const [integerPart, decimals] = (entero ? String(absolute) : absolute.toFixed(2)).split('.');
  const withDots = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${sign}$${withDots}${decimals ? `,${decimals}` : ''}`;
}
