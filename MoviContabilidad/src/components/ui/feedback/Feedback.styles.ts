import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radii.md,
    borderWidth: sizes.hairline,
  },
  bannerTexts: { flex: 1, gap: spacing.xxs },
  bannerActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  state: { alignItems: 'center', justifyContent: 'center', gap: spacing.md, paddingVertical: spacing['2xl'], paddingHorizontal: spacing.xl },
  stateCompact: { paddingVertical: spacing.lg },
  stateIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.decoration.goldWash,
    borderWidth: sizes.hairline,
    borderColor: colors.decoration.goldSoft,
  },
  skeleton: { backgroundColor: colors.background.sunken },
});
