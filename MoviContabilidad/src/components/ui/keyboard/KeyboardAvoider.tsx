/**
 * Empuja el contenido por encima del teclado. En Android la app es
 * edge-to-edge (la ventana no se redimensiona), así que `behavior` va en las
 * dos plataformas, como recomienda la guía de teclado de Expo.
 *
 * Sin `keyboardVerticalOffset`: el encabezado de la app (AppHeader, un
 * `header` de JS) y el contenido de la pantalla son hermanos dentro de un
 * contenedor que empieza en el borde superior de la ventana. La posición del
 * contenido ya incluye el alto del encabezado; sumarlo otra vez dejaba un
 * hueco de ese alto entre la banda de comandos y el teclado.
 */
import type { PropsWithChildren } from 'react';
import { KeyboardAvoidingView, type StyleProp, type ViewStyle } from 'react-native';

export function KeyboardAvoider({ style, children }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return (
    <KeyboardAvoidingView behavior="padding" style={[{ flex: 1 }, style]}>
      {children}
    </KeyboardAvoidingView>
  );
}
