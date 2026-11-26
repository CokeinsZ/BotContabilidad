import { StyleSheet } from 'react-native';

import { colors, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  line: { height: sizes.hairline, backgroundColor: colors.decoration.gold, alignSelf: 'stretch' },
  short: { width: 48, height: 2, borderRadius: 1, backgroundColor: colors.decoration.gold },
  ornament: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, width: 160 },
  ornamentLine: { flex: 1, height: sizes.hairline, backgroundColor: colors.decoration.gold },
  diamond: { width: 7, height: 7, backgroundColor: colors.decoration.gold, transform: [{ rotate: '45deg' }] },
});
