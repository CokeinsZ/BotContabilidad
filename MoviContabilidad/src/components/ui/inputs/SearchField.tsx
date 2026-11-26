import { colors } from '@/theme';

import { IconButton } from '../buttons';
import { Icon } from '../icons';
import { TextField, type TextFieldProps } from './TextField';

export interface SearchFieldProps extends Omit<TextFieldProps, 'value' | 'onChange' | 'onChangeText'> {
  value: string;
  onChange: (value: string) => void;
}

export function SearchField({ value, onChange, placeholder = 'Buscar', ...rest }: SearchFieldProps) {
  return (
    <TextField
      value={value}
      onChangeText={onChange}
      placeholder={placeholder}
      returnKeyType="search"
      autoCorrect={false}
      autoCapitalize="none"
      leading={<Icon name="buscar" size="sm" color={colors.text.secondary} />}
      trailing={
        value ? <IconButton icon="cerrar" size={32} accessibilityLabel="Borrar búsqueda" onPress={() => onChange('')} /> : null
      }
      {...rest}
    />
  );
}
