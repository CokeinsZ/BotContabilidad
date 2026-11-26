import { useEffect, useState } from 'react';
import { Animated } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '@/theme';

import { Icon } from '../../icons';
import { Text } from '../../typography';
import { styles } from './Toast.styles';

export type ToastTone = 'success' | 'info' | 'danger';

const ICON = { success: 'exito', info: 'info', danger: 'error' } as const;
const ICON_COLOR = { success: colors.action.primarySoftPressed, info: colors.text.inverse, danger: colors.status.danger.border };

export function Toast({ tone, message }: { tone: ToastTone; message: string }) {
  const insets = useSafeAreaInsets();
  const [opacity] = useState(() => new Animated.Value(0));
  useEffect(() => {
    Animated.timing(opacity, { toValue: 1, duration: 160, useNativeDriver: true }).start();
  }, [opacity]);
  return (
    <Animated.View
      pointerEvents="none"
      accessibilityLiveRegion="polite"
      style={[styles.container, { bottom: insets.bottom + spacing['2xl'], opacity }]}
    >
      <Animated.View style={styles.toast}>
        <Icon name={ICON[tone]} size="sm" color={ICON_COLOR[tone]} />
        <Text variant="captionStrong" tone="inverse">
          {message}
        </Text>
      </Animated.View>
    </Animated.View>
  );
}
