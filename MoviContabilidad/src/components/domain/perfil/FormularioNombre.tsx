import type { Control } from 'react-hook-form';

import { Button } from '@/components/ui/buttons';
import { Banner } from '@/components/ui/feedback';
import { FormField, TextField } from '@/components/ui/inputs';
import { Column, Screen } from '@/components/ui/layout';
import { limpiarNombre } from '@/utils/text/limpiarNombre';

/** Reglas del bot (src/mobile/profile_service.py): entre 2 y 80 caracteres. */
export const NOMBRE_MIN = 2;
export const NOMBRE_MAX = 80;

export interface FormularioNombreValores {
  nombre: string;
}

export interface FormularioNombreProps {
  control: Control<FormularioNombreValores>;
  etiqueta: string;
  /** Qué pasa al cambiarlo (p. ej. "Se usará en las planillas nuevas"). */
  nota: string;
  onSubmit: () => void;
  guardando: boolean;
  /** Falso mientras el nombre sea el mismo de antes. */
  puedeGuardar: boolean;
}

/** Pantalla completa para cambiar un nombre (negocio o administrador). Lo usan dos pantallas. */
export function FormularioNombre({ control, etiqueta, nota, onSubmit, guardando, puedeGuardar }: FormularioNombreProps) {
  return (
    <Screen
      scroll
      footer={
        <Button label="Guardar" icon="check" size="lg" fullWidth loading={guardando} disabled={!puedeGuardar} onPress={onSubmit} />
      }
    >
      <Column gap="lg">
        <FormField<FormularioNombreValores>
          control={control}
          name="nombre"
          rules={{
            validate: (value) => {
              const length = limpiarNombre(value).length;
              return (length >= NOMBRE_MIN && length <= NOMBRE_MAX) || `Debe tener entre ${NOMBRE_MIN} y ${NOMBRE_MAX} caracteres.`;
            },
          }}
          render={({ value, onChange, onBlur, error }) => (
            <TextField
              label={etiqueta}
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={error}
              autoCapitalize="words"
              returnKeyType="done"
              onSubmitEditing={puedeGuardar ? onSubmit : undefined}
              maxLength={NOMBRE_MAX + 20}
            />
          )}
        />
        <Banner tone="info" message={nota} />
      </Column>
    </Screen>
  );
}
