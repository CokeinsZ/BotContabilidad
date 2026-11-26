import { View } from 'react-native';

import { toneColors, type Tone } from '@/theme';

import { Button, IconButton } from '../buttons';
import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { styles } from './Feedback.styles';

const ICON: Record<Tone, IconName> = {
  neutral: 'info',
  info: 'info',
  success: 'exito',
  warning: 'aviso',
  danger: 'error',
  gold: 'tocar',
};

export interface BannerProps {
  tone?: Tone;
  title?: string;
  message: string;
  icon?: IconName;
  action?: { label: string; onPress: () => void };
  onDismiss?: () => void;
}

/** Aviso dentro de la pantalla (sin conexión con Google, sección llena, pistas). */
export function Banner({ tone = 'info', title, message, icon, action, onDismiss }: BannerProps) {
  const colors = toneColors(tone);
  return (
    <View style={[styles.banner, { backgroundColor: colors.bg, borderColor: colors.border }]} accessibilityRole="summary">
      <Icon name={icon ?? ICON[tone]} size="md" color={colors.icon} />
      <View style={styles.bannerTexts}>
        {title ? <Text variant="bodyStrong" style={{ color: colors.fg }}>{title}</Text> : null}
        <Text variant="caption" tone="strong">
          {message}
        </Text>
        {action ? (
          <View style={styles.bannerActions}>
            <Button label={action.label} size="sm" variant="secondary" onPress={action.onPress} />
          </View>
        ) : null}
      </View>
      {onDismiss ? <IconButton icon="cerrar" size={32} accessibilityLabel="Cerrar aviso" onPress={onDismiss} /> : null}
    </View>
  );
}
