import { View } from 'react-native';

import { Text } from '@/components/ui/typography';

import { styles } from '../EdicionPlanillaScreen.styles';

/** "24-11-2026 · Hoja 2" y el negocio debajo (en el encabezado). */
export function TituloPlanilla({ titulo, subtitulo }: { titulo: string; subtitulo: string }) {
  return (
    <View style={styles.title}>
      <Text variant="heading" numberOfLines={1} accessibilityRole="header">
        {titulo}
      </Text>
      {subtitulo ? (
        <Text variant="micro" numberOfLines={1}>
          {subtitulo}
        </Text>
      ) : null}
    </View>
  );
}
