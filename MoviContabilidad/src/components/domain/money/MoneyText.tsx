import { Text, type TextProps } from '@/components/ui/typography';
import { formatearMonto } from '@/utils/money/formatearMonto';

export interface MoneyTextProps extends Omit<TextProps, 'children' | 'variant'> {
  value: number | null;
  variant?: 'amount' | 'amountSmall' | 'amountLarge';
}

/** Montos como los escribe el bot ($5.000), en tinta; solo un negativo va en rojo. */
export function MoneyText({ value, variant = 'amount', tone, ...rest }: MoneyTextProps) {
  const negative = value !== null && value < 0;
  return (
    <Text variant={variant} tone={tone ?? (negative ? 'danger' : 'primary')} {...rest}>
      {formatearMonto(value)}
    </Text>
  );
}
