import { ActivityIndicator, Pressable, type StyleProp, type ViewStyle } from 'react-native';

import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { buttonPalettes, styles, type ButtonSize, type ButtonVariant } from './Button.styles';

export interface ButtonProps {
  label: string;
  onPress?: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: IconName;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/** Botón único de la app: primario, secundario, contorno, fantasma o peligro. */
export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  disabled = false,
  fullWidth = false,
  accessibilityHint,
  style,
  testID,
}: ButtonProps) {
  const palette = buttonPalettes[variant];
  const isDisabled = disabled || loading;
  const iconNode = icon ? <Icon name={icon} size={size === 'sm' ? 'sm' : 'md'} color={palette.fg} /> : null;
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      disabled={isDisabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        styles[size],
        { backgroundColor: pressed ? palette.pressedBg : palette.bg, borderColor: palette.border },
        fullWidth && styles.fullWidth,
        isDisabled && styles.disabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={palette.fg} />
      ) : (
        <>
          {iconPosition === 'left' ? iconNode : null}
          <Text variant={size === 'sm' ? 'buttonSmall' : 'button'} style={{ color: palette.fg }}>
            {label}
          </Text>
          {iconPosition === 'right' ? iconNode : null}
        </>
      )}
    </Pressable>
  );
}
