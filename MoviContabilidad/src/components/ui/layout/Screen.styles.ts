import { StyleSheet } from 'react-native';

import { colors, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  fill: { flex: 1 },
  padded: { paddingHorizontal: spacing.gutter },
  scrollContent: { flexGrow: 1, gap: spacing.lg },
  footer: {
    paddingHorizontal: spacing.gutter,
    paddingTop: spacing.md,
    borderTopWidth: sizes.hairline,
    borderTopColor: colors.border.subtle,
    backgroundColor: colors.background.screen,
  },
});
