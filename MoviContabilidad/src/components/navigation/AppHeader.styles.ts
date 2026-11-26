import { StyleSheet } from 'react-native';

import { colors, spacing } from '@/theme';

export const styles = StyleSheet.create({
  container: { backgroundColor: colors.background.screen },
  bar: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
  },
  side: { minWidth: 44, alignItems: 'flex-start', justifyContent: 'center' },
  title: { flex: 1, justifyContent: 'center', paddingHorizontal: spacing.xs },
  right: { flexDirection: 'row', alignItems: 'center', gap: spacing.xxs },
});
