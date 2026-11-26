import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export const buttonPalettes: Record<ButtonVariant, { bg: string; pressedBg: string; fg: string; border: string }> = {
  primary: { bg: colors.action.primary, pressedBg: colors.action.primaryPressed, fg: colors.text.inverse, border: colors.action.primary },
  secondary: { bg: colors.action.primarySoft, pressedBg: colors.action.primarySoftPressed, fg: colors.text.success, border: colors.action.primarySoft },
  outline: { bg: colors.background.screen, pressedBg: colors.background.surface, fg: colors.text.primary, border: colors.border.default },
  ghost: { bg: 'transparent', pressedBg: colors.action.primarySoft, fg: colors.text.action, border: 'transparent' },
  danger: { bg: colors.background.screen, pressedBg: colors.status.danger.bg, fg: colors.text.danger, border: colors.border.danger },
};

export const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderRadius: radii.md,
    borderWidth: sizes.hairline,
    paddingHorizontal: spacing.lg,
  },
  sm: { minHeight: sizes.control.sm, paddingHorizontal: spacing.md },
  md: { minHeight: sizes.control.md },
  lg: { minHeight: sizes.control.lg, paddingHorizontal: spacing.xl },
  fullWidth: { alignSelf: 'stretch' },
  disabled: { opacity: 0.5 },
});
