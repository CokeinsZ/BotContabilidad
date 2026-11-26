import { Pressable, View } from 'react-native';

import { toneColors, type Tone } from '@/theme';

import { Button } from '../../buttons';
import { Icon, type IconName } from '../../icons';
import { Text } from '../../typography';
import type { AlertKind } from './alert.types';
import { styles } from './AlertDialog.styles';

const KIND: Record<AlertKind, { icon: IconName; tone: Tone }> = {
  info: { icon: 'info', tone: 'info' },
  exito: { icon: 'exito', tone: 'success' },
  aviso: { icon: 'aviso', tone: 'warning' },
  error: { icon: 'error', tone: 'danger' },
  pregunta: { icon: 'ayuda', tone: 'gold' },
};

export interface AlertDialogProps {
  kind: AlertKind;
  title: string;
  message?: string;
  closeText: string;
  confirm?: { text: string; destructive: boolean };
  onClose: () => void;
  onConfirm?: () => void;
}

export function AlertDialog({ kind, title, message, closeText, confirm, onClose, onConfirm }: AlertDialogProps) {
  const { icon, tone } = KIND[kind];
  const colors = toneColors(tone);
  return (
    <Pressable style={styles.overlay} onPress={onClose} accessibilityViewIsModal>
      <Pressable style={styles.dialog} onPress={() => undefined} accessibilityRole="alert">
        <View style={[styles.iconBox, { backgroundColor: colors.bg }]}>
          <Icon name={icon} size="lg" color={colors.icon} />
        </View>
        <Text variant="title">{title}</Text>
        {message ? <Text tone="secondary">{message}</Text> : null}
        <View style={styles.buttons}>
          <Button label={closeText} variant={confirm ? 'outline' : 'primary'} onPress={onClose} style={styles.button} />
          {confirm ? (
            <Button
              label={confirm.text}
              variant={confirm.destructive ? 'danger' : 'primary'}
              onPress={onConfirm}
              style={styles.button}
            />
          ) : null}
        </View>
      </Pressable>
    </Pressable>
  );
}
