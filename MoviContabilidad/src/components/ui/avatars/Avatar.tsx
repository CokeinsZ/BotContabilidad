import { StyleSheet, View } from 'react-native';

import { colors, fonts, sizes } from '@/theme';
import { iniciales } from '@/utils/text/iniciales';

import { Text } from '../typography';

export interface AvatarProps {
  name: string;
  size?: keyof typeof sizes.avatar;
  /** monogram = aro dorado y letra Playfair (negocio, trabajador en su detalle). */
  variant?: 'plain' | 'monogram';
}

export function Avatar({ name, size = 'md', variant = 'plain' }: AvatarProps) {
  const pixels = sizes.avatar[size];
  const monogram = variant === 'monogram';
  return (
    <View
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={[
        styles.avatar,
        { width: pixels, height: pixels, borderRadius: pixels / 2 },
        monogram && styles.monogram,
      ]}
    >
      <Text
        maxFontSizeMultiplier={1}
        style={{
          fontFamily: monogram ? fonts.display : fonts.semibold,
          fontSize: Math.round(pixels * (monogram ? 0.38 : 0.36)),
          color: monogram ? colors.text.success : colors.text.strong,
        }}
      >
        {iniciales(name)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  avatar: { alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background.sunken },
  monogram: {
    backgroundColor: colors.action.primarySoft,
    borderWidth: 1.5,
    borderColor: colors.decoration.gold,
    boxShadow: `inset 0px 0px 0px 3px ${colors.background.screen}`,
  },
});
