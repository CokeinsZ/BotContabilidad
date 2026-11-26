import type { ReactElement } from 'react';
import { Controller, type Control, type FieldValues, type Path, type RegisterOptions } from 'react-hook-form';

export interface FormFieldState<V> {
  value: V;
  onChange: (value: V) => void;
  onBlur: () => void;
  error?: string;
}

export interface FormFieldProps<T extends FieldValues, V> {
  control: Control<T>;
  name: Path<T>;
  rules?: RegisterOptions<T, Path<T>>;
  /** Pinta CUALQUIER campo con el estado del formulario (ZoneUp lo ataba a TextInput). */
  render: (field: FormFieldState<V>) => ReactElement;
}

/** Conecta react-hook-form con cualquier input de la app. */
export function FormField<T extends FieldValues, V = string>({ control, name, rules, render }: FormFieldProps<T, V>) {
  return (
    <Controller
      control={control}
      name={name}
      rules={rules}
      render={({ field, fieldState }) =>
        render({ value: field.value as V, onChange: field.onChange, onBlur: field.onBlur, error: fieldState.error?.message })
      }
    />
  );
}
