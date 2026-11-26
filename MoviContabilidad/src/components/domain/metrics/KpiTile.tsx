import { StyleSheet, View } from 'react-native';

import { Text } from '@/components/ui/typography';
import { spacing } from '@/theme';

import { MoneyText } from '../money';

export interface KpiTileProps {
  label: string;
  value: number | null;
  /** El total que más importa (saldo total): cifra grande. */
  emphasis?: boolean;
}

export function KpiTile({ label, value, emphasis = false }: KpiTileProps) {
  return (
    <View style={styles.tile} accessible accessibilityLabel={`${label}: ${value ?? 'sin dato'}`}>
      <Text variant="caption">{label}</Text>
      <MoneyText value={value} variant={emphasis ? 'amountLarge' : 'amount'} numberOfLines={1} adjustsFontSizeToFit />
    </View>
  );
}

const styles = StyleSheet.create({
  tile: { flex: 1, minWidth: 0, gap: spacing.xxs },
});
