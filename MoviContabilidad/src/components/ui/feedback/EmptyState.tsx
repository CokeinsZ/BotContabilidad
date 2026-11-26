import { View } from 'react-native';

import { colors } from '@/theme';

import { Button } from '../buttons';
import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { styles } from './Feedback.styles';

export interface EmptyStateProps {
  icon?: IconName;
  title: string;
  message?: string;
  action?: { label: string; onPress: () => void; icon?: IconName };
  compact?: boolean;
  /** Tono del ícono: dorado (vacío) o rojo (error). */
  iconColor?: string;
}

export function EmptyState({ icon = 'info', title, message, action, compact = false, iconColor }: EmptyStateProps) {
  return (
    <View style={[styles.state, compact && styles.stateCompact]}>
      <View style={styles.stateIcon}>
        <Icon name={icon} size="lg" color={iconColor ?? colors.decoration.goldIcon} />
      </View>
      <Text variant="heading" align="center">
        {title}
      </Text>
      {message ? (
        <Text tone="secondary" align="center">
          {message}
        </Text>
      ) : null}
      {action ? <Button label={action.label} icon={action.icon} onPress={action.onPress} variant="secondary" /> : null}
    </View>
  );
}
