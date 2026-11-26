import type { RefObject } from 'react';
import { Platform, TextInput, View } from 'react-native';

import type { TextInputRef } from '@/components/ui/inputs';
import { colors } from '@/theme';

import { BotonEnviar } from './BotonEnviar';
import { styles } from './Composer.styles';
import { PrefijoComando } from './PrefijoComando';

/** En la web el campo es de una línea: un textarea no crece solo y queda muy alto. */
const WEB = Platform.OS === 'web';

interface ComposerProps {
  inputRef: RefObject<TextInputRef | null>;
  etiqueta: string | null;
  texto: string;
  placeholder: string;
  puedeEnviar: boolean;
  onTexto: (texto: string) => void;
  onBorrarVacio: () => void;
  onEnviar: () => void;
}

/** Barra de escritura: prefijo del comando + texto + enviar. */
export function Composer({ inputRef, etiqueta, texto, placeholder, puedeEnviar, onTexto, onBorrarVacio, onEnviar }: ComposerProps) {
  return (
    <View style={styles.container}>
      <View style={styles.field}>
        {etiqueta ? <PrefijoComando etiqueta={etiqueta} /> : null}
        <TextInput
          ref={inputRef}
          style={styles.input}
          value={texto}
          onChangeText={onTexto}
          onKeyPress={(event) => {
            if (event.nativeEvent.key === 'Backspace' && texto === '') onBorrarVacio();
          }}
          placeholder={placeholder}
          placeholderTextColor={colors.text.muted}
          selectionColor={colors.action.primary}
          cursorColor={colors.action.primary}
          accessibilityLabel={etiqueta ? `Mensaje de ${etiqueta}` : 'Mensaje'}
          multiline={!WEB}
          // Web: la tecla Enter del teclado envía y el teclado sigue abierto.
          enterKeyHint={WEB ? 'send' : undefined}
          blurOnSubmit={WEB ? false : undefined}
          onSubmitEditing={WEB && puedeEnviar ? onEnviar : undefined}
          autoCorrect={false}
          autoCapitalize="none"
        />
      </View>
      <BotonEnviar onPress={onEnviar} disabled={!puedeEnviar} />
    </View>
  );
}
