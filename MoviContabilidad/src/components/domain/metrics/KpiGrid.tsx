import { StyleSheet, View } from 'react-native';

import { colors, sizes, spacing } from '@/theme';

import { KpiTile, type KpiTileProps } from './KpiTile';

/** Fila de KPIs entre dos separadores (tarjeta de hoy, resumen). */
export function KpiGrid({ items, columns = 3 }: { items: KpiTileProps[]; columns?: number }) {
  const rows: KpiTileProps[][] = [];
  for (let index = 0; index < items.length; index += columns) rows.push(items.slice(index, index + columns));
  return (
    <View style={styles.grid}>
      {rows.map((row, rowIndex) => (
        <View key={rowIndex} style={styles.row}>
          {row.map((item) => (
            <KpiTile key={item.label} {...item} />
          ))}
          {Array.from({ length: columns - row.length }, (_, index) => (
            <View key={`hueco-${index}`} style={styles.filler} />
          ))}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    gap: spacing.md,
    paddingVertical: spacing.md,
    borderTopWidth: sizes.hairline,
    borderBottomWidth: sizes.hairline,
    borderColor: colors.border.subtle,
  },
  row: { flexDirection: 'row', gap: spacing.md },
  filler: { flex: 1 },
});
