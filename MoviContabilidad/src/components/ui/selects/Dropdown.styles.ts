import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  container: { gap: spacing.xs },
  trigger: {
    minHeight: sizes.control.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.md,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.surface,
  },
  triggerPressed: { backgroundColor: colors.background.sunken },
  triggerText: { flex: 1 },
  option: {
    minHeight: sizes.touchTarget + 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.sm,
  },
  optionPressed: { backgroundColor: colors.background.surface },
  optionSelected: { backgroundColor: colors.action.primarySoft },
  optionDisabled: { opacity: 0.45 },
  optionTexts: { flex: 1, gap: spacing.xxs },
});
