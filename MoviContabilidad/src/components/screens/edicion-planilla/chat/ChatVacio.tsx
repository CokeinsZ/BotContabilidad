import { View } from 'react-native';

import { EmptyState } from '@/components/ui/feedback';

import { styles } from '../EdicionPlanillaScreen.styles';

export function ChatVacio() {
  return (
    <View style={styles.empty}>
      <EmptyState
        icon="libre"
        title="Registra el primer movimiento"
        message="Elige un comando abajo, escribe el monto y envía. El historial de este chat queda solo en tu teléfono."
      />
    </View>
  );
}
