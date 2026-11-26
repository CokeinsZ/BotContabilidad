import { StyleSheet } from 'react-native';

import { colors, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  item: {
    minHeight: sizes.touchTarget + 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingVertical: spacing.sm,
    // Listas a todo el ancho: el texto se alinea con el margen de la pantalla.
    paddingHorizontal: spacing.gutter,
    backgroundColor: colors.background.screen,
  },
  pressed: { backgroundColor: colors.action.primarySoft },
  disabled: { opacity: 0.5 },
  texts: { flex: 1, gap: spacing.xxs },
  separator: { height: sizes.hairline, backgroundColor: colors.border.subtle },
  sectionHeader: {
    paddingHorizontal: spacing.gutter,
    paddingTop: spacing.md,
    paddingBottom: spacing.xs,
    backgroundColor: colors.background.screen,
  },
});
