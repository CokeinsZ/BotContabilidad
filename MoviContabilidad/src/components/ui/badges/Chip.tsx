import { Pressable } from 'react-native';

import { colors } from '@/theme';

import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { styles } from './Chip.styles';

export interface ChipProps {
  label: string;
  icon?: IconName | (string & {});
  selected?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  accessibilityLabel?: string;
  accessibilityHint?: string;
}

/** Chip seleccionable: banda de comandos, sugerencias de trabajadores y opciones del bot. */
export function Chip({ label, icon, selected = false, disabled = false, onPress, accessibilityLabel, accessibilityHint }: ChipProps) {
  const fg = selected ? colors.text.inverse : colors.text.strong;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ selected, disabled }}
      disabled={disabled}
      onPress={onPress}
      hitSlop={6}
      style={({ pressed }) => [styles.chip, pressed && !selected && styles.pressed, selected && styles.selected, disabled && styles.disabled]}
    >
      {icon ? <Icon name={icon} size="sm" color={selected ? colors.text.inverse : colors.text.secondary} /> : null}
      <Text variant="captionStrong" style={{ color: fg }}>
        {label}
      </Text>
    </Pressable>
  );
}
