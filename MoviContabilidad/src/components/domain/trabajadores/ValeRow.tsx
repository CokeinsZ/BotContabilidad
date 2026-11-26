import { StyleSheet, View } from 'react-native';

import type { Vale } from '@/api/entities';
import { Text } from '@/components/ui/typography';
import { colors, sizes, spacing } from '@/theme';
import { diaCorto } from '@/utils/dates/fechaRelativa';

import { MoneyText } from '../money';

/** Un vale del archivo del trabajador: fecha y monto. */
export function ValeRow({ vale }: { vale: Vale }) {
  return (
    <View style={styles.row}>
      <View style={styles.texts}>
        <Text variant="bodyStrong">{vale.fecha ? diaCorto(vale.fecha) : 'Sin fecha'}</Text>
        <Text variant="micro" tone="secondary">
          {vale.nota ?? vale.fecha ?? `Fila ${vale.fila}`}
        </Text>
      </View>
      <MoneyText value={vale.monto} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: sizes.touchTarget + 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingVertical: spacing.sm,
    borderTopWidth: sizes.hairline,
    borderTopColor: colors.border.subtle,
  },
  texts: { flex: 1, gap: spacing.xxs },
});
