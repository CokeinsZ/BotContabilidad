import type { PropsWithChildren } from 'react';
import { Pressable, View, type StyleProp, type ViewStyle } from 'react-native';

import { spacing, type SpacingToken } from '@/theme';

import { cardVariants, styles, type CardVariant } from './Card.styles';

export interface CardProps {
  variant?: CardVariant;
  padding?: SpacingToken;
  gap?: SpacingToken;
  onPress?: () => void;
  onLongPress?: () => void;
  accessibilityLabel?: string;
  style?: StyleProp<ViewStyle>;
}

/** Superficie con borde (sobre blanco separa mejor el borde que la sombra). */
export function Card({
  variant = 'outlined',
  padding = 'lg',
  gap = 'md',
  onPress,
  onLongPress,
  accessibilityLabel,
  style,
  children,
}: PropsWithChildren<CardProps>) {
  const base = [styles.card, cardVariants[variant], { padding: spacing[padding], gap: spacing[gap] }];
  if (onPress || onLongPress) {
    return (
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
        onPress={onPress}
        onLongPress={onLongPress}
        style={({ pressed }) => [...base, pressed && styles.pressed, style]}
      >
        {children}
      </Pressable>
    );
  }
  return <View style={[...base, style]}>{children}</View>;
}
