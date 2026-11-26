import { View } from 'react-native';

import { IconButton } from '@/components/ui/buttons';
import type { IconName } from '@/components/ui/icons';

import { styles } from './AppHeader.styles';

export interface HeaderAction {
  icon: IconName;
  label: string;
  onPress: () => void;
}

/** Botones a la derecha del encabezado (Resumen, Abrir en Google Sheets…). */
export function HeaderActions({ actions }: { actions: HeaderAction[] }) {
  return (
    <View style={styles.right}>
      {actions.map((action) => (
        <IconButton key={action.label} icon={action.icon} accessibilityLabel={action.label} onPress={action.onPress} />
      ))}
    </View>
  );
}
