import type { TextStyle } from 'react-native';

import { fonts } from './fonts';

/** Escala tipográfica (ver plan §8.5). Los montos usan cifras tabulares. */
export const typography = {
  display: { fontFamily: fonts.display, fontSize: 30, lineHeight: 36 },
  title: { fontFamily: fonts.semibold, fontSize: 22, lineHeight: 28 },
  heading: { fontFamily: fonts.semibold, fontSize: 17, lineHeight: 24 },
  body: { fontFamily: fonts.regular, fontSize: 15, lineHeight: 22 },
  bodyStrong: { fontFamily: fonts.medium, fontSize: 15, lineHeight: 22 },
  caption: { fontFamily: fonts.regular, fontSize: 13, lineHeight: 18 },
  captionStrong: { fontFamily: fonts.medium, fontSize: 13, lineHeight: 18 },
  micro: { fontFamily: fonts.regular, fontSize: 11, lineHeight: 14 },
  overline: { fontFamily: fonts.semibold, fontSize: 11, lineHeight: 16, letterSpacing: 1.2, textTransform: 'uppercase' },
  amount: { fontFamily: fonts.semibold, fontSize: 17, lineHeight: 24, fontVariant: ['tabular-nums'] },
  amountSmall: { fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18, fontVariant: ['tabular-nums'] },
  amountLarge: { fontFamily: fonts.bold, fontSize: 28, lineHeight: 34, fontVariant: ['tabular-nums'] },
  code: { fontFamily: fonts.semibold, fontSize: 32, lineHeight: 40, letterSpacing: 6, fontVariant: ['tabular-nums'] },
  button: { fontFamily: fonts.semibold, fontSize: 15, lineHeight: 20 },
  buttonSmall: { fontFamily: fonts.semibold, fontSize: 13, lineHeight: 18 },
} satisfies Record<string, TextStyle>;

export type TypographyVariant = keyof typeof typography;
