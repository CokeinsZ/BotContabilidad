import { View } from 'react-native';

import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

import { styles } from './VincularScreen.styles';

const PASOS = ['Toca "Abrir WhatsApp"', 'Envía el mensaje sin cambiarlo', 'Vuelve aquí: entras solo'];

export function PasosVinculacion() {
  return (
    <View style={styles.steps}>
      {PASOS.map((paso, index) => (
        <View key={paso} style={styles.step}>
          <View style={[styles.stepNumber, { borderColor: colors.decoration.gold }]}>
            <Text variant="captionStrong" tone="gold">
              {index + 1}
            </Text>
          </View>
          <Text>{paso}</Text>
        </View>
      ))}
    </View>
  );
}
