import type { PropsWithChildren, ReactNode } from 'react';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { spacing } from '@/theme';

import { Text } from '../typography';

export interface SectionProps {
  /** Sobrelínea dorada en mayúsculas ("PLANILLA DE HOY"). */
  overline?: string;
  title?: string;
  action?: ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function Section({ overline, title, action, style, children }: PropsWithChildren<SectionProps>) {
  return (
    <View style={[styles.section, style]}>
      {overline || title || action ? (
        <View style={styles.header}>
          <View style={styles.texts}>
            {overline ? <Text variant="overline">{overline}</Text> : null}
            {title ? (
              <Text variant="heading" accessibilityRole="header">
                {title}
              </Text>
            ) : null}
          </View>
          {action}
        </View>
      ) : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: spacing.md },
  header: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: spacing.md },
  texts: { flex: 1, gap: spacing.xxs },
});
