import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing, typography } from '@/theme';

export const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  field: {
    flex: 1,
    minHeight: 42,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    borderRadius: radii.xl,
    borderWidth: sizes.hairline,
    borderColor: colors.border.focus,
    backgroundColor: colors.background.screen,
  },
  prefix: { paddingVertical: spacing.sm },
  input: { flex: 1, maxHeight: 110, paddingVertical: spacing.sm, color: colors.text.primary, ...typography.body },
});
