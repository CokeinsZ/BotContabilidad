import { Pressable, View } from 'react-native';

import type { OpcionSeleccion, Seleccion } from '@/api/entities';
import { Button } from '@/components/ui/buttons';
import { Icon } from '@/components/ui/icons';
import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

import { styles as screenStyles } from '../EdicionPlanillaScreen.styles';
import { styles } from './Chat.styles';

interface OpcionesSeleccionProps {
  seleccion: Seleccion;
  ocupado: boolean;
  onElegir: (opcion: OpcionSeleccion) => void;
  onCancelar: () => void;
}

/** El menú numerado de WhatsApp como botones. La banda espera la respuesta. */
export function OpcionesSeleccion({ seleccion, ocupado, onElegir, onCancelar }: OpcionesSeleccionProps) {
  return (
    <View style={screenStyles.panel} accessibilityRole="menu">
      <Text variant="bodyStrong">{seleccion.pregunta}</Text>
      {seleccion.opciones.map((opcion) => (
        <Pressable
          key={opcion.valor}
          accessibilityRole="menuitem"
          accessibilityLabel={opcion.etiqueta}
          accessibilityState={{ disabled: ocupado }}
          disabled={ocupado}
          onPress={() => onElegir(opcion)}
          style={({ pressed }) => [styles.option, pressed && styles.optionPressed]}
        >
          {opcion.crea ? (
            <Icon name="agregar" size="sm" color={colors.action.primary} />
          ) : (
            <View style={styles.optionNumber}>
              <Text variant="micro" tone="success">
                {opcion.valor}
              </Text>
            </View>
          )}
          <Text variant="bodyStrong" tone={opcion.crea ? 'action' : 'primary'} style={{ flex: 1 }}>
            {opcion.etiqueta}
          </Text>
        </Pressable>
      ))}
      <Text variant="micro">Si no eliges, se cancela «{seleccion.comando}» y se borra de la planilla.</Text>
      <Button label="Cancelar" variant="danger" size="sm" onPress={onCancelar} disabled={ocupado} />
    </View>
  );
}
