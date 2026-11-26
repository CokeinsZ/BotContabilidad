import { Pressable } from 'react-native';

import { colors, toneColors } from '@/theme';

import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { BottomSheet } from './BottomSheet';
import { styles } from './BottomSheet.styles';

export interface SheetAction {
  id: string;
  label: string;
  icon: IconName;
  tone?: 'default' | 'danger';
  onPress: () => void;
}

export interface ActionSheetProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  actions: SheetAction[];
}

/** Lista de acciones desde abajo (mantener presionada una planilla). Cierra antes de ejecutar. */
export function ActionSheet({ visible, onClose, title, actions }: ActionSheetProps) {
  return (
    <BottomSheet visible={visible} onClose={onClose} title={title}>
      {actions.map((action) => {
        const color = action.tone === 'danger' ? toneColors('danger').fg : colors.text.primary;
        return (
          <Pressable
            key={action.id}
            accessibilityRole="button"
            accessibilityLabel={action.label}
            onPress={() => {
              onClose();
              action.onPress();
            }}
            style={({ pressed }) => [styles.action, pressed && styles.actionPressed]}
          >
            <Icon name={action.icon} size="md" color={action.tone === 'danger' ? color : colors.action.primary} />
            <Text variant="bodyStrong" style={{ color }}>
              {action.label}
            </Text>
          </Pressable>
        );
      })}
    </BottomSheet>
  );
}
