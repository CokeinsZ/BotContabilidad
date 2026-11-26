import { Pressable, type StyleProp, type ViewStyle } from 'react-native';

import { sizes } from '@/theme';

import { Icon, type IconName } from '../icons';
import { iconButtonPalettes, styles, type IconButtonVariant } from './IconButton.styles';

export interface IconButtonProps {
  icon: IconName;
  /** Obligatorio: es lo que lee el lector de pantalla. */
  accessibilityLabel: string;
  onPress?: () => void;
  variant?: IconButtonVariant;
  /** Diámetro del botón (el área táctil nunca baja de 44). */
  size?: number;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

export function IconButton({
  icon,
  accessibilityLabel,
  onPress,
  variant = 'plain',
  size = 40,
  disabled = false,
  style,
  testID,
}: IconButtonProps) {
  const palette = iconButtonPalettes[variant];
  const slop = Math.max(0, (sizes.touchTarget - size) / 2);
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      hitSlop={slop}
      style={({ pressed }) => [
        styles.base,
        { width: size, height: size, backgroundColor: pressed ? palette.pressedBg : palette.bg, borderColor: palette.border },
        disabled && styles.disabled,
        style,
      ]}
    >
      <Icon name={icon} size={size >= 44 ? 'lg' : 'md'} color={palette.fg} />
    </Pressable>
  );
}
