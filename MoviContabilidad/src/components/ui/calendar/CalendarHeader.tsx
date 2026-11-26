import { View } from 'react-native';

import { etiquetaMes } from '@/utils/dates/meses';
import type { MesAnio } from '@/utils/dates/fechaPlanilla';

import { IconButton } from '../buttons';
import { Text } from '../typography';
import { styles } from './Calendar.styles';

interface CalendarHeaderProps {
  month: MesAnio;
  onPrevious: () => void;
  onNext: () => void;
}

export function CalendarHeader({ month, onPrevious, onNext }: CalendarHeaderProps) {
  return (
    <View style={styles.header}>
      <IconButton icon="izquierda" accessibilityLabel="Mes anterior" onPress={onPrevious} />
      <Text variant="heading" accessibilityRole="header">
        {etiquetaMes(month.anio, month.mes)}
      </Text>
      <IconButton icon="derecha" accessibilityLabel="Mes siguiente" onPress={onNext} />
    </View>
  );
}
