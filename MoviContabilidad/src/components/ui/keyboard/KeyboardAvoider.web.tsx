/**
 * Web: no hace falta empujar nada. La raíz de la app ya mide solo la parte
 * visible de la pantalla cuando el teclado está abierto (VisualViewportRoot).
 */
import type { PropsWithChildren } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

export function KeyboardAvoider({ style, children }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return <View style={[{ flex: 1 }, style]}>{children}</View>;
}
