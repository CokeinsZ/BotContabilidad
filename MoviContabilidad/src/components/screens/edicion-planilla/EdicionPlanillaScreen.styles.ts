import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  fill: { flex: 1 },
  banner: { paddingHorizontal: spacing.md, paddingTop: spacing.sm },
  footer: {
    borderTopWidth: sizes.hairline,
    borderTopColor: colors.border.subtle,
    backgroundColor: colors.background.screen,
  },
  title: { gap: 0 },
  empty: { flex: 1, justifyContent: 'center', paddingHorizontal: spacing.xl },
  panel: {
    marginHorizontal: spacing.md,
    marginTop: spacing.sm,
    padding: spacing.md,
    gap: spacing.sm,
    borderRadius: radii.lg,
    borderWidth: sizes.hairline,
    borderColor: colors.decoration.goldSoft,
    backgroundColor: colors.decoration.goldWash,
  },
});
