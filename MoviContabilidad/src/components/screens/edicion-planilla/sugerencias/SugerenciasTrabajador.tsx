import { ScrollView, StyleSheet } from 'react-native';

import type { Trabajador } from '@/api/entities';
import { Chip } from '@/components/ui/badges';
import { spacing } from '@/theme';

/** Nombres que coinciden con lo escrito (Vale / Nómina): evitan el menú de "varios parecidos". */
export function SugerenciasTrabajador({ trabajadores, onElegir }: { trabajadores: Trabajador[]; onElegir: (nombre: string) => void }) {
  if (trabajadores.length === 0) return null;
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} keyboardShouldPersistTaps="always" contentContainerStyle={styles.row}>
      {trabajadores.map((trabajador) => (
        <Chip key={trabajador.id} label={trabajador.nombre} icon="perfil" onPress={() => onElegir(trabajador.nombre)} />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { gap: spacing.sm, paddingHorizontal: spacing.md, paddingTop: spacing.sm },
});
