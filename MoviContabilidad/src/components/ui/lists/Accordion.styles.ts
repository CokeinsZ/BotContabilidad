import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  container: {
    borderRadius: radii.lg,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    overflow: 'hidden',
    backgroundColor: colors.background.screen,
  },
  header: {
    minHeight: sizes.touchTarget + 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  headerPressed: { backgroundColor: colors.background.surface },
  texts: { flex: 1, gap: spacing.xxs },
  content: { borderTopWidth: sizes.hairline, borderTopColor: colors.border.subtle },
});
