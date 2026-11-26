import { StyleSheet } from 'react-native';

import { spacing } from '@/theme';

export const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  date: { flex: 1.3 },
  sheet: { flex: 1 },
  legend: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingHorizontal: spacing.xs },
  legendDot: { width: 6, height: 6, borderRadius: 3 },
});
