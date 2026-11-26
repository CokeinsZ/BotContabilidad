import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  tile: {
    flex: 1,
    minHeight: 96,
    padding: spacing.md,
    gap: spacing.xxs,
    borderRadius: radii.lg,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.screen,
  },
  wide: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, minHeight: 64 },
  featured: { backgroundColor: colors.action.primary, borderColor: colors.decoration.gold },
  pressed: { backgroundColor: colors.background.surface },
  featuredPressed: { backgroundColor: colors.action.primaryPressed },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: radii.sm,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.action.primarySoft,
    marginBottom: spacing.xs,
  },
  iconBoxWide: { marginBottom: 0 },
  iconBoxFeatured: { backgroundColor: 'rgba(255, 255, 255, 0.14)' },
  texts: { flex: 1, gap: spacing.xxs },
});
