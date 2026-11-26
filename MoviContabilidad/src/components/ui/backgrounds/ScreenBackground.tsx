import type { PropsWithChildren } from 'react';
import { StyleSheet, View, type StyleProp, type ViewStyle } from 'react-native';

import { colors } from '@/theme';

import { HeroWatermark } from './patterns/HeroWatermark';
import { LedgerLines } from './patterns/LedgerLines';

export type ScreenBackgroundVariant = 'plain' | 'hero' | 'ledger';

export interface ScreenBackgroundProps {
  variant?: ScreenBackgroundVariant;
  /** Texto de la marca de agua del fondo `hero` (p. ej. el monograma del negocio). */
  watermark?: string;
  style?: StyleProp<ViewStyle>;
}

/** Fondo de toda pantalla: siempre blanco puro; `hero` y `ledger` agregan un patrón muy suave. */
export function ScreenBackground({ variant = 'plain', watermark, style, children }: PropsWithChildren<ScreenBackgroundProps>) {
  return (
    <View style={[styles.background, style]}>
      {variant === 'ledger' ? <LedgerLines /> : null}
      {variant === 'hero' && watermark ? <HeroWatermark text={watermark} /> : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  background: { flex: 1, backgroundColor: colors.background.screen, overflow: 'hidden' },
});
