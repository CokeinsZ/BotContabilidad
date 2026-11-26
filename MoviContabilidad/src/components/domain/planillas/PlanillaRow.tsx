import { StyleSheet, View } from 'react-native';

import type { Planilla } from '@/api/entities';
import { Icon } from '@/components/ui/icons';
import { Text } from '@/components/ui/typography';
import { colors, sizes, spacing } from '@/theme';
import { diaCorto } from '@/utils/dates/fechaRelativa';

import { HojaBadge } from './HojaBadge';

export interface PlanillaRowProps {
  planilla: Planilla;
  pressed?: boolean;
  chevron?: boolean;
}

/** Fila de una planilla: "Mar 24 nov", nombre del archivo y la hoja. */
export function PlanillaRow({ planilla, pressed = false, chevron = true }: PlanillaRowProps) {
  return (
    <View style={[styles.row, pressed && styles.pressed]}>
      <View style={styles.texts}>
        <Text variant="bodyStrong">{diaCorto(planilla.fecha)}</Text>
        <Text variant="micro" tone="secondary" style={styles.fileName}>
          {planilla.nombre}
        </Text>
      </View>
      <HojaBadge hoja={planilla.hoja} />
      {chevron ? <Icon name="derecha" size="sm" color={colors.text.muted} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: sizes.touchTarget + 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderTopWidth: sizes.hairline,
    borderTopColor: colors.border.subtle,
    backgroundColor: colors.background.screen,
  },
  pressed: { backgroundColor: colors.action.primarySoft },
  texts: { flex: 1, gap: spacing.xxs },
  fileName: { fontVariant: ['tabular-nums'] },
});
