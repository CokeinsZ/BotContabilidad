import { useState, type ComponentRef, type ReactNode, type Ref } from 'react';
import { TextInput, View, type StyleProp, type TextInputProps, type TextStyle, type ViewStyle } from 'react-native';

import { colors } from '@/theme';

import { Text } from '../typography';
import { styles } from './TextField.styles';

export interface TextFieldProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  helper?: string;
  error?: string | null;
  leading?: ReactNode;
  trailing?: ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
  inputStyle?: StyleProp<TextStyle>;
  ref?: Ref<TextInputRef>;
}

export type TextInputRef = ComponentRef<typeof TextInput>;

/** Campo base de la app: etiqueta, ayuda, error y accesorios a los lados. */
export function TextField({
  label,
  helper,
  error,
  leading,
  trailing,
  containerStyle,
  inputStyle,
  onFocus,
  onBlur,
  editable = true,
  multiline,
  ref,
  ...input
}: TextFieldProps) {
  const [focused, setFocused] = useState(false);
  return (
    <View style={[styles.container, containerStyle]}>
      {label ? (
        <Text variant="captionStrong" tone="secondary">
          {label}
        </Text>
      ) : null}
      <View style={[styles.field, focused && styles.focused, !!error && styles.error, !editable && styles.disabled]}>
        {leading}
        <TextInput
          ref={ref}
          style={[styles.input, multiline && styles.multiline, inputStyle]}
          placeholderTextColor={colors.text.muted}
          selectionColor={colors.action.primary}
          cursorColor={colors.action.primary}
          accessibilityLabel={label}
          editable={editable}
          multiline={multiline}
          onFocus={(event) => {
            setFocused(true);
            onFocus?.(event);
          }}
          onBlur={(event) => {
            setFocused(false);
            onBlur?.(event);
          }}
          {...input}
        />
        {trailing}
      </View>
      {error ? (
        <Text variant="caption" tone="danger">
          {error}
        </Text>
      ) : helper ? (
        <Text variant="caption">{helper}</Text>
      ) : null}
    </View>
  );
}
