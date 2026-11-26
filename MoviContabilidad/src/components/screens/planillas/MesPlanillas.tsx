import { View } from 'react-native';

import type { MesPlanillas as Mes, Planilla } from '@/api/entities';
import { ErrorState, Skeleton } from '@/components/ui/feedback';
import { Accordion } from '@/components/ui/lists';
import { Text } from '@/components/ui/typography';
import { useMesPlanillas } from '@/hooks/screens/planillas/useMesPlanillas';

import { FilaPlanillaInteractiva } from './FilaPlanillaInteractiva';
import { styles } from './PlanillasScreen.styles';

interface MesPlanillasProps {
  mes: Mes;
  abierto: boolean;
  onAlternar: () => void;
  onAbrir: (planilla: Planilla) => void;
  onAbrirEnSheets: (planilla: Planilla) => void;
  onAcciones: (planilla: Planilla) => void;
}

/** Una carpeta mes-aaaa de Drive como lista desplegable. */
export function MesPlanillas({ mes, abierto, onAlternar, ...acciones }: MesPlanillasProps) {
  const { planillas, cargando, error, reintentar, subtitulo } = useMesPlanillas(mes, abierto);
  return (
    <Accordion title={mes.etiqueta} subtitle={subtitulo} expanded={abierto} onToggle={onAlternar}>
      {cargando ? (
        <View style={styles.loading}>
          <Skeleton height={18} />
          <Skeleton height={18} />
        </View>
      ) : error ? (
        <ErrorState compact message={error} onRetry={reintentar} />
      ) : planillas.length === 0 ? (
        <View style={styles.monthEmpty}>
          <Text tone="secondary">No hay planillas en este mes.</Text>
        </View>
      ) : (
        planillas.map((planilla) => <FilaPlanillaInteractiva key={planilla.id} planilla={planilla} {...acciones} />)
      )}
    </Accordion>
  );
}
