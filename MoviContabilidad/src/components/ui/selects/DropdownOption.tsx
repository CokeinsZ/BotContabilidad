import { Pressable, View } from 'react-native';

import { colors } from '@/theme';

import { Icon } from '../icons';
import { Text } from '../typography';
import { styles } from './Dropdown.styles';

export interface DropdownOptionData<V> {
  value: V;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface DropdownOptionProps<V> {
  option: DropdownOptionData<V>;
  selected: boolean;
  onPress: () => void;
}

export function DropdownOption<V>({ option, selected, onPress }: DropdownOptionProps<V>) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={option.description ? `${option.label}. ${option.description}` : option.label}
      accessibilityState={{ selected, disabled: !!option.disabled }}
      disabled={option.disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.option,
        selected && styles.optionSelected,
        pressed && styles.optionPressed,
        option.disabled && styles.optionDisabled,
      ]}
    >
      <View style={styles.optionTexts}>
        <Text variant="bodyStrong">{option.label}</Text>
        {option.description ? <Text variant="caption">{option.description}</Text> : null}
      </View>
      {selected ? <Icon name="check" size="md" color={colors.action.primary} /> : null}
    </Pressable>
  );
}
