import { Badge } from '@/components/ui/badges';

/** "Hoja 2". Las adicionales (2, 3…) van en dorado suave para distinguirlas. */
export function HojaBadge({ hoja }: { hoja: number }) {
  return <Badge label={`Hoja ${hoja}`} tone={hoja > 1 ? 'gold' : 'neutral'} />;
}
