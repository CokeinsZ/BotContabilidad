import { StyleSheet } from 'react-native';

import { colors, radii, shadows, spacing } from '@/theme';

export const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: colors.background.overlay },
  sheet: {
    maxHeight: '80%',
    paddingTop: spacing.sm,
    borderTopLeftRadius: radii.xl,
    borderTopRightRadius: radii.xl,
    backgroundColor: colors.background.screen,
    ...shadows.sheet,
  },
  handle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 2,
    marginBottom: spacing.sm,
    backgroundColor: colors.border.default,
  },
  title: { paddingHorizontal: spacing.gutter, paddingBottom: spacing.sm },
  action: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, minHeight: 52, paddingHorizontal: spacing.gutter },
  actionPressed: { backgroundColor: colors.background.surface },
});
