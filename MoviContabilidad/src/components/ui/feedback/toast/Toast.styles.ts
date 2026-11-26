import { StyleSheet } from 'react-native';

import { colors, radii, shadows, spacing } from '@/theme';

export const styles = StyleSheet.create({
  container: { position: 'absolute', left: spacing.gutter, right: spacing.gutter, zIndex: 900, elevation: 900, alignItems: 'center' },
  toast: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: radii.pill,
    backgroundColor: colors.text.primary,
    ...shadows.toast,
  },
});
