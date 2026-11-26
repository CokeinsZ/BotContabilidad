import type { PropsWithChildren } from 'react';
import { Modal, Pressable, ScrollView, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { spacing } from '@/theme';

import { Text } from '../typography';
import { styles } from './BottomSheet.styles';

export interface BottomSheetProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
}

/** Hoja inferior genérica (opciones de un selector, acciones de una planilla). */
export function BottomSheet({ visible, onClose, title, children }: PropsWithChildren<BottomSheetProps>) {
  const insets = useSafeAreaInsets();
  return (
    <Modal visible={visible} transparent animationType="fade" statusBarTranslucent navigationBarTranslucent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} accessibilityLabel="Cerrar" accessibilityRole="button">
        <Pressable style={[styles.sheet, { paddingBottom: insets.bottom + spacing.md }]} onPress={() => undefined}>
          <View style={styles.handle} />
          {title ? (
            <Text variant="heading" style={styles.title} accessibilityRole="header">
              {title}
            </Text>
          ) : null}
          <ScrollView bounces={false}>{children}</ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}
