import { StyleSheet } from 'react-native';

import { spacing } from '@/theme';

export const styles = StyleSheet.create({
  list: { padding: spacing.gutter, gap: spacing.md, paddingBottom: 120 },
  loading: { gap: spacing.md, padding: spacing.lg },
  monthEmpty: { padding: spacing.lg },
});
