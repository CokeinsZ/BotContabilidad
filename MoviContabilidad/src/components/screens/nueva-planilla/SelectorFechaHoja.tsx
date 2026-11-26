import { View } from 'react-native';

import { DateField } from '@/components/ui/inputs';
import { Dropdown } from '@/components/ui/selects';
import type { OpcionHoja } from '@/utils/planillas/disponibilidadHojas';

import { styles } from './NuevaPlanillaScreen.styles';

interface SelectorFechaHojaProps {
  texto: string;
  onTexto: (texto: string) => void;
  errorFecha: string | null;
  opciones: OpcionHoja[];
  hoja: number;
  onHoja: (hoja: number) => void;
}

/** Fecha y hoja en una fila: Primera (por defecto), Segunda, Tercera… */
export function SelectorFechaHoja({ texto, onTexto, errorFecha, opciones, hoja, onHoja }: SelectorFechaHojaProps) {
  return (
    <View style={styles.row}>
      <DateField label="Fecha" value={texto} onChange={onTexto} error={errorFecha} containerStyle={styles.date} />
      <Dropdown
        label="Hoja"
        title="¿Qué hoja del día?"
        value={hoja}
        onChange={onHoja}
        style={styles.sheet}
        options={opciones.map((opcion) => ({
          value: opcion.hoja,
          label: opcion.etiqueta,
          description: opcion.descripcion,
          disabled: !opcion.disponible,
        }))}
      />
    </View>
  );
}
