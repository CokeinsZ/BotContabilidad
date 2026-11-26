import { View } from 'react-native';

import { errorMessage } from '@/api';
import { FloatingActionButton } from '@/components/ui/buttons';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/feedback';
import { ScreenBackground } from '@/components/ui/backgrounds';
import { usePlanillasScreen } from '@/hooks/screens/planillas/usePlanillasScreen';

import { AccionesPlanillaSheet } from './AccionesPlanillaSheet';
import { ListaMeses } from './ListaMeses';
import { PistaDobleToque } from './PistaDobleToque';

export default function PlanillasScreen() {
  const s = usePlanillasScreen();
  const { meses } = s;
  return (
    <ScreenBackground>
      {meses.isLoading ? (
        <LoadingState message="Leyendo las carpetas de Drive…" />
      ) : meses.error && !meses.data ? (
        <ErrorState message={errorMessage(meses.error)} onRetry={() => void meses.refetch()} />
      ) : (
        <ListaMeses
          meses={meses.data ?? []}
          estaAbierto={s.estaAbierto}
          onAlternar={s.alternarMes}
          onAbrir={s.abrir}
          onAbrirEnSheets={s.abrirEnSheets}
          onAcciones={s.mostrarAcciones}
          refrescando={s.refrescando}
          onRefrescar={s.refrescar}
          encabezado={s.pistaVisible ? <View><PistaDobleToque onCerrar={s.cerrarPista} /></View> : null}
          vacio={
            <EmptyState
              icon="carpeta"
              title="Todavía no hay planillas"
              message="Crea la primera y aparecerá aquí, agrupada por mes como en Google Drive."
              action={{ label: 'Crear la primera', onPress: s.nueva, icon: 'crearPlanilla' }}
            />
          }
        />
      )}
      <FloatingActionButton icon="agregar" accessibilityLabel="Nueva planilla" onPress={s.nueva} />
      <AccionesPlanillaSheet
        planilla={s.conAcciones}
        onCerrar={s.cerrarAcciones}
        onAbrir={s.abrir}
        onResumen={s.verResumen}
        onAbrirEnSheets={s.abrirEnSheets}
        onCopiarEnlace={s.copiarEnlace}
      />
    </ScreenBackground>
  );
}
