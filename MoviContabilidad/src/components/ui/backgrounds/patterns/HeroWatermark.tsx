import { StyleSheet, View } from 'react-native';

import { colors, fonts } from '@/theme';

import { Text } from '../../typography';

interface HeroWatermarkProps {
  text: string;
}

/** Monograma gigante al 4 % detrás del encabezado (Principal, Vincular). */
export function HeroWatermark({ text }: HeroWatermarkProps) {
  return (
    <View style={styles.container} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <Text style={styles.text} maxFontSizeMultiplier={1}>
        {text}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { position: 'absolute', top: -24, left: 0, right: 0, alignItems: 'center' },
  text: { fontFamily: fonts.display, fontSize: 220, lineHeight: 240, color: colors.text.primary, opacity: 0.04 },
});
