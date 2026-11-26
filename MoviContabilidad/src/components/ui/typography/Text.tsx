import { Text as RNText, type TextProps as RNTextProps } from 'react-native';

import { typography, type TypographyVariant } from '@/theme';

import { textTones, type TextTone } from './Text.styles';

export interface TextProps extends RNTextProps {
  variant?: TypographyVariant;
  tone?: TextTone;
  align?: 'left' | 'center' | 'right';
}

const DEFAULT_TONE: Partial<Record<TypographyVariant, TextTone>> = {
  overline: 'gold',
  caption: 'secondary',
  micro: 'secondary',
};

/** El único componente de texto de la app. */
export function Text({ variant = 'body', tone, align, style, maxFontSizeMultiplier = 1.6, ...rest }: TextProps) {
  return (
    <RNText
      maxFontSizeMultiplier={maxFontSizeMultiplier}
      style={[
        typography[variant],
        { color: textTones[tone ?? DEFAULT_TONE[variant] ?? 'primary'] },
        align ? { textAlign: align } : null,
        style,
      ]}
      {...rest}
    />
  );
}
