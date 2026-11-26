import { StyleSheet } from 'react-native';

import { spacing } from '@/theme';

export const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  headerTexts: { flex: 1, gap: spacing.xxs },
  todayTitle: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.sm },
  tiles: { gap: spacing.md },
  tileRow: { flexDirection: 'row', gap: spacing.md },
  skeleton: { gap: spacing.sm },
});
