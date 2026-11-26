import { StyleSheet } from 'react-native';

import { colors, radii, shadows, spacing } from '@/theme';

export const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: 1000,
    elevation: 1000,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: colors.background.overlay,
  },
  dialog: {
    width: '100%',
    maxWidth: 380,
    padding: spacing.xl,
    gap: spacing.md,
    borderRadius: radii.xl,
    backgroundColor: colors.background.screen,
    ...shadows.toast,
  },
  iconBox: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  buttons: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  button: { flex: 1 },
});
