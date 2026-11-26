import { StyleSheet, View } from 'react-native';

import type { UsoSeccion } from '@/api/entities';
import { Banner } from '@/components/ui/feedback';
import { ProgressBar } from '@/components/ui/progress';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';
import { spacing } from '@/theme';

/** Cuántas filas lleva cada sección, antes de que el bot rechace un movimiento. */
export function UsoSecciones({ secciones, hayLlenas, onCrearSegunda }: { secciones: UsoSeccion[]; hayLlenas: boolean; onCrearSegunda: () => void }) {
  return (
    <Card>
      <Text variant="overline">Filas usadas por sección</Text>
      {secciones.map((seccion) => (
        <View key={seccion.id} style={styles.row}>
          <View style={styles.texts}>
            <Text variant="captionStrong">{seccion.etiqueta}</Text>
            <Text variant="micro">
              {seccion.usadas === null ? 'Sin dato' : `${seccion.usadas} de ${seccion.capacidad}`}
            </Text>
          </View>
          <ProgressBar value={seccion.usadas ?? 0} max={seccion.capacidad} accessibilityLabel={seccion.etiqueta} />
        </View>
      ))}
      {hayLlenas ? (
        <Banner
          tone="warning"
          title="Hay una sección llena"
          message="Para seguir registrando en esa sección, crea una planilla adicional del día."
          action={{ label: 'Crear segunda planilla', onPress: onCrearSegunda }}
        />
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.xs },
  texts: { flexDirection: 'row', justifyContent: 'space-between' },
});
