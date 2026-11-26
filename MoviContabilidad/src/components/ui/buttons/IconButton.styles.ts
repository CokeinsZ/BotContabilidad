import { StyleSheet } from 'react-native';

import { colors, radii, sizes } from '@/theme';

export type IconButtonVariant = 'plain' | 'tonal' | 'outline' | 'primary';

export const iconButtonPalettes: Record<IconButtonVariant, { bg: string; pressedBg: string; fg: string; border: string }> = {
  plain: { bg: 'transparent', pressedBg: colors.background.surface, fg: colors.text.strong, border: 'transparent' },
  tonal: { bg: colors.action.primarySoft, pressedBg: colors.action.primarySoftPressed, fg: colors.action.primary, border: colors.action.primarySoft },
  outline: { bg: colors.background.screen, pressedBg: colors.background.surface, fg: colors.text.strong, border: colors.border.default },
  primary: { bg: colors.action.primary, pressedBg: colors.action.primaryPressed, fg: colors.text.inverse, border: colors.action.primary },
};

export const styles = StyleSheet.create({
  base: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: sizes.hairline,
    borderRadius: radii.pill,
  },
  disabled: { opacity: 0.4 },
});
