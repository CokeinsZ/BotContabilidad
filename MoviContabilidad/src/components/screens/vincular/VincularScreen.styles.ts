import { StyleSheet } from 'react-native';

import { spacing } from '@/theme';

export const styles = StyleSheet.create({
  content: { alignItems: 'center', gap: spacing.lg, paddingTop: spacing['2xl'] },
  heading: { alignItems: 'center', gap: spacing.xs },
  subtitle: { maxWidth: 280 },
  buttons: { alignSelf: 'stretch', gap: spacing.sm },
  code: { alignSelf: 'stretch', alignItems: 'center', gap: spacing.xxs },
  steps: { alignSelf: 'stretch', gap: spacing.md },
  step: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  stepNumber: { width: 26, height: 26, borderRadius: 13, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  status: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, justifyContent: 'center' },
});
