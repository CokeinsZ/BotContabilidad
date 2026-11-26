import type { PropsWithChildren } from 'react';
import { Keyboard, Pressable, type StyleProp, type ViewStyle } from 'react-native';

/** Tocar aquí oculta el teclado (en el chat: tocar los mensajes deja más espacio para verlos). */
export function DismissKeyboardArea({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return (
    <Pressable style={[{ flex: 1 }, style]} onPress={Keyboard.dismiss} accessible={false}>
      {children}
    </Pressable>
  );
}
