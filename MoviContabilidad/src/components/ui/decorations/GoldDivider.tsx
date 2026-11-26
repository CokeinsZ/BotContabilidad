import { View, type StyleProp, type ViewStyle } from 'react-native';

import { styles } from './GoldDivider.styles';

export interface GoldDividerProps {
  /** line = filete de 1 px; short = trazo corto; ornament = línea–rombo–línea. */
  variant?: 'line' | 'short' | 'ornament';
  style?: StyleProp<ViewStyle>;
}

/** La firma visual de la app: el dorado solo como filete (ver plan §8.4). */
export function GoldDivider({ variant = 'line', style }: GoldDividerProps) {
  if (variant === 'ornament') {
    return (
      <View style={[styles.ornament, style]} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <View style={styles.ornamentLine} />
        <View style={styles.diamond} />
        <View style={styles.ornamentLine} />
      </View>
    );
  }
  return <View style={[variant === 'short' ? styles.short : styles.line, style]} />;
}
