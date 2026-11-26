import { ScrollView, StyleSheet } from 'react-native';

import type { Comando } from '@/api/entities';
import { Chip } from '@/components/ui/badges';
import { spacing } from '@/theme';

const LIBRE = 'libre';

interface BandaComandosProps {
  comandos: Comando[];
  seleccionado: string | null;
  deshabilitada: boolean;
  deshacerDisponible: boolean;
  onElegir: (comando: Comando | typeof LIBRE) => void;
}

/** Una sola línea, desplazable, siempre visible encima del teclado. */
export function BandaComandos({ comandos, seleccionado, deshabilitada, deshacerDisponible, onElegir }: BandaComandosProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      keyboardShouldPersistTaps="always"
      contentContainerStyle={styles.band}
      accessibilityRole="toolbar"
      accessibilityLabel="Comandos"
    >
      <Chip
        label="Libre"
        icon="libre"
        selected={seleccionado === LIBRE}
        disabled={deshabilitada}
        accessibilityHint="Escribe como en WhatsApp, varios movimientos a la vez"
        onPress={() => onElegir(LIBRE)}
      />
      {comandos.map((comando) => (
        <Chip
          key={comando.id}
          label={comando.etiqueta}
          icon={comando.icono}
          selected={seleccionado === comando.id}
          disabled={deshabilitada || (comando.id === 'deshacer' && !deshacerDisponible)}
          accessibilityHint={comando.ayuda}
          onPress={() => onElegir(comando)}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  band: { gap: spacing.sm, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
});
