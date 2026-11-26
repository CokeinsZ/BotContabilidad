/**
 * Toque, doble toque y mantener presionado en el mismo elemento.
 *
 * Si hay `onDoubleTap`, el toque simple espera ~260 ms por si llega el
 * segundo (es inevitable). La respuesta visual al presionar sí es inmediata.
 * Con lector de pantalla, "mantener" ofrece las mismas acciones.
 */
import { useEffect, useRef, type ReactNode } from 'react';
import { Pressable, type PressableStateCallbackType, type StyleProp, type ViewStyle } from 'react-native';

export interface TapAreaProps {
  onPress?: () => void;
  onDoubleTap?: () => void;
  onLongPress?: () => void;
  delayMs?: number;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle> | ((state: PressableStateCallbackType) => StyleProp<ViewStyle>);
  children: ReactNode | ((state: PressableStateCallbackType) => ReactNode);
  testID?: string;
}

export function TapArea({
  onPress,
  onDoubleTap,
  onLongPress,
  delayMs = 260,
  accessibilityLabel,
  accessibilityHint,
  style,
  children,
  testID,
}: TapAreaProps) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  const handlePress = () => {
    if (!onDoubleTap) {
      onPress?.();
      return;
    }
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
      onDoubleTap();
      return;
    }
    timer.current = setTimeout(() => {
      timer.current = null;
      onPress?.();
    }, delayMs);
  };

  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityActions={onLongPress ? [{ name: 'longpress', label: 'Más acciones' }] : undefined}
      onAccessibilityAction={(event) => {
        if (event.nativeEvent.actionName === 'longpress') onLongPress?.();
      }}
      onPress={handlePress}
      onLongPress={onLongPress}
      delayLongPress={400}
      style={style}
    >
      {children}
    </Pressable>
  );
}
