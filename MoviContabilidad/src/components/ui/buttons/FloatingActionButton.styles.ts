import { StyleSheet } from 'react-native';

import { colors, radii, shadows, spacing } from '@/theme';

export const styles = StyleSheet.create({
  fab: {
    position: 'absolute',
    right: spacing.gutter,
    width: 56,
    height: 56,
    borderRadius: radii.xl,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.action.primary,
    ...shadows.floating,
  },
  pressed: { backgroundColor: colors.action.primaryPressed },
});
