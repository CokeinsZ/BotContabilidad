import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing, typography } from '@/theme';

export const styles = StyleSheet.create({
  container: { gap: spacing.xs },
  field: {
    minHeight: sizes.control.md,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.md,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.surface,
  },
  focused: {
    borderColor: colors.border.focus,
    backgroundColor: colors.background.screen,
    boxShadow: `0px 0px 0px 3px ${colors.action.focusRing}`,
  },
  error: { borderColor: colors.text.danger },
  disabled: { opacity: 0.6 },
  input: {
    flex: 1,
    paddingVertical: spacing.sm,
    color: colors.text.primary,
    ...typography.body,
  },
  multiline: { minHeight: 88, textAlignVertical: 'top' },
});
