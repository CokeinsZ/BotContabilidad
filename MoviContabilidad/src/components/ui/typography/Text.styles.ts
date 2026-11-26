import { colors } from '@/theme';

export const textTones = {
  primary: colors.text.primary,
  strong: colors.text.strong,
  secondary: colors.text.secondary,
  muted: colors.text.muted,
  inverse: colors.text.inverse,
  gold: colors.text.gold,
  action: colors.text.action,
  danger: colors.text.danger,
  warning: colors.text.warning,
  success: colors.text.success,
} as const;

export type TextTone = keyof typeof textTones;
