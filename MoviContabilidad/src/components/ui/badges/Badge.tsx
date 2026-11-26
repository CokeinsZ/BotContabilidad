import { StyleSheet, View } from 'react-native';

import { radii, sizes, spacing, toneColors, type Tone } from '@/theme';

import { Icon, type IconName } from '../icons';
import { Text } from '../typography';

export interface BadgeProps {
  label: string;
  tone?: Tone;
  icon?: IconName;
}

export function Badge({ label, tone = 'neutral', icon }: BadgeProps) {
  const colors = toneColors(tone);
  return (
    <View style={[styles.badge, { backgroundColor: colors.bg, borderColor: colors.border }]}>
      {icon ? <Icon name={icon} size={12} color={colors.icon} /> : null}
      <Text variant="micro" style={{ color: colors.fg }}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: radii.pill,
    borderWidth: sizes.hairline,
  },
});
