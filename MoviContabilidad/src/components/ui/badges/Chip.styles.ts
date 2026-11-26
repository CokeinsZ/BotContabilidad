import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  chip: {
    minHeight: 34,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    borderRadius: radii.pill,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.screen,
  },
  pressed: { backgroundColor: colors.background.surface },
  selected: { backgroundColor: colors.action.primary, borderColor: colors.decoration.gold },
  disabled: { opacity: 0.4 },
});
