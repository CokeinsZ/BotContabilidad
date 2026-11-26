import { StyleSheet } from 'react-native';

import { colors, radii, sizes } from '@/theme';

export type CardVariant = 'outlined' | 'tinted' | 'gold';

export const cardVariants = StyleSheet.create({
  outlined: { backgroundColor: colors.background.screen, borderColor: colors.border.default },
  tinted: { backgroundColor: colors.background.surface, borderColor: colors.border.subtle },
  gold: { backgroundColor: colors.decoration.goldWash, borderColor: colors.decoration.goldSoft },
});

export const styles = StyleSheet.create({
  card: { borderRadius: radii.lg, borderWidth: sizes.hairline, overflow: 'hidden' },
  pressed: { backgroundColor: colors.background.surface },
});
