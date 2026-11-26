import { colors } from '@/theme';
import { aplicarMascaraFecha } from '@/utils/dates/mascaraFecha';

import { Icon } from '../icons';
import { TextField, type TextFieldProps } from './TextField';

export interface DateFieldProps extends Omit<TextFieldProps, 'value' | 'onChange' | 'onChangeText' | 'keyboardType' | 'maxLength'> {
  value: string;
  onChange: (value: string) => void;
}

/** Fecha dd-mm-aaaa: teclado numérico y guiones automáticos. */
export function DateField({ value, onChange, placeholder = 'dd-mm-aaaa', ...rest }: DateFieldProps) {
  return (
    <TextField
      value={value}
      onChangeText={(text) => onChange(aplicarMascaraFecha(text))}
      keyboardType="number-pad"
      maxLength={10}
      placeholder={placeholder}
      autoCorrect={false}
      trailing={<Icon name="calendario" size="sm" color={colors.text.secondary} />}
      {...rest}
    />
  );
}
