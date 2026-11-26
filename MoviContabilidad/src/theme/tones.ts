import { colors, type StatusTone } from './colors';

export type Tone = StatusTone | 'neutral';

/** Colores de un tono (Badge, Banner, burbujas del bot, ProgressBar). */
export function toneColors(tone: Tone) {
  if (tone === 'neutral') {
    return { fg: colors.text.strong, bg: colors.background.surface, border: colors.border.default, icon: colors.text.secondary };
  }
  return colors.status[tone];
}
