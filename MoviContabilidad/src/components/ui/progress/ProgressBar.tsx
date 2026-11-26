import { StyleSheet, View } from 'react-native';

import { colors, radii, toneColors, type Tone } from '@/theme';

export interface ProgressBarProps {
  value: number;
  max: number;
  /** Por defecto según ocupación: >75 % aviso, 100 % peligro. */
  tone?: Tone;
  height?: number;
  accessibilityLabel?: string;
}

export function ProgressBar({ value, max, tone, height = 6, accessibilityLabel }: ProgressBarProps) {
  const ratio = max > 0 ? Math.min(1, Math.max(0, value / max)) : 0;
  const autoTone: Tone = ratio >= 1 ? 'danger' : ratio > 0.75 ? 'warning' : 'success';
  const fill = toneColors(tone ?? autoTone).icon;
  return (
    <View
      accessibilityRole="progressbar"
      accessibilityLabel={accessibilityLabel}
      accessibilityValue={{ min: 0, max, now: value }}
      style={[styles.track, { height, borderRadius: height / 2 }]}
    >
      <View style={{ width: `${ratio * 100}%`, height, borderRadius: radii.pill, backgroundColor: fill }} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: { width: '100%', overflow: 'hidden', backgroundColor: colors.background.sunken },
});
