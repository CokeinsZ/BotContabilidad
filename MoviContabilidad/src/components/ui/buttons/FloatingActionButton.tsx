import { Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '@/theme';

import { Icon, type IconName } from '../icons';
import { styles } from './FloatingActionButton.styles';

export interface FloatingActionButtonProps {
  icon: IconName;
  accessibilityLabel: string;
  onPress: () => void;
}

export function FloatingActionButton({ icon, accessibilityLabel, onPress }: FloatingActionButtonProps) {
  const insets = useSafeAreaInsets();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      style={({ pressed }) => [styles.fab, { bottom: insets.bottom + spacing.xl }, pressed && styles.pressed]}
    >
      <Icon name={icon} size="lg" color={colors.text.inverse} />
    </Pressable>
  );
}
