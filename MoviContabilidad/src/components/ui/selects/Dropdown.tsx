import { useState } from 'react';
import { Pressable, View, type StyleProp, type ViewStyle } from 'react-native';

import { colors } from '@/theme';

import { Icon } from '../icons';
import { BottomSheet } from '../overlays';
import { Text } from '../typography';
import { styles } from './Dropdown.styles';
import { DropdownOption, type DropdownOptionData } from './DropdownOption';

export interface DropdownProps<V extends string | number> {
  label?: string;
  value: V | null;
  options: DropdownOptionData<V>[];
  onChange: (value: V) => void;
  placeholder?: string;
  /** Título de la hoja de opciones (por defecto, la etiqueta). */
  title?: string;
  style?: StyleProp<ViewStyle>;
}

/** Selector: abre una hoja inferior con las opciones (las deshabilitadas explican por qué). */
export function Dropdown<V extends string | number>({
  label,
  value,
  options,
  onChange,
  placeholder = 'Elegir',
  title,
  style,
}: DropdownProps<V>) {
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value);
  return (
    <View style={[styles.container, style]}>
      {label ? (
        <Text variant="captionStrong" tone="secondary">
          {label}
        </Text>
      ) : null}
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${label ?? 'Opción'}: ${selected?.label ?? placeholder}`}
        accessibilityHint="Abre la lista de opciones"
        onPress={() => setOpen(true)}
        style={({ pressed }) => [styles.trigger, pressed && styles.triggerPressed]}
      >
        <Text style={styles.triggerText} numberOfLines={1} tone={selected ? 'primary' : 'muted'}>
          {selected?.label ?? placeholder}
        </Text>
        <Icon name="abajo" size="sm" color={colors.text.secondary} />
      </Pressable>
      <BottomSheet visible={open} onClose={() => setOpen(false)} title={title ?? label}>
        {options.map((option) => (
          <DropdownOption
            key={String(option.value)}
            option={option}
            selected={option.value === value}
            onPress={() => {
              onChange(option.value);
              setOpen(false);
            }}
          />
        ))}
      </BottomSheet>
    </View>
  );
}
