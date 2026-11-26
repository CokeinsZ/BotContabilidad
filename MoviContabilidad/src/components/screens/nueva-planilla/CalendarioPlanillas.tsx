import { View } from 'react-native';

import { Calendar } from '@/components/ui/calendar';
import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';
import type { MesAnio } from '@/utils/dates/fechaPlanilla';

import { styles } from './NuevaPlanillaScreen.styles';

interface CalendarioPlanillasProps {
  mes: MesAnio;
  onMes: (mes: MesAnio) => void;
  seleccionado: string | null;
  onSeleccionar: (fecha: string) => void;
  hoy: string;
  marcas: Record<string, number>;
}

/** Calendario con un punto dorado por cada hoja que ya existe ese día. */
export function CalendarioPlanillas(props: CalendarioPlanillasProps) {
  return (
    <View>
      <Calendar
        month={props.mes}
        onMonthChange={props.onMes}
        selected={props.seleccionado}
        onSelect={props.onSeleccionar}
        today={props.hoy}
        marks={props.marcas}
      />
      <View style={styles.legend}>
        <View style={[styles.legendDot, { backgroundColor: colors.decoration.goldIcon }]} />
        <Text variant="micro">Cada punto es una hoja que ya existe ese día.</Text>
      </View>
    </View>
  );
}
