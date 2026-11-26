import { Stack } from 'expo-router';

import { errorMessage } from '@/api';
import { Button } from '@/components/ui/buttons';
import { ErrorState, LoadingState } from '@/components/ui/feedback';
import { Column, Screen } from '@/components/ui/layout';
import { useResumenPlanillaScreen } from '@/hooks/screens/resumen-planilla/useResumenPlanillaScreen';
import { tituloPlanilla } from '@/utils/planillas/ordinales';

import { TotalesPlanilla } from './TotalesPlanilla';
import { UsoSecciones } from './UsoSecciones';

export default function ResumenPlanillaScreen() {
  const s = useResumenPlanillaScreen();
  const { resumen } = s;
  if (resumen.isLoading) return <LoadingState message="Leyendo la planilla…" />;
  if (!resumen.data) {
    return <ErrorState message={resumen.error ? errorMessage(resumen.error) : 'Sin datos.'} onRetry={() => void resumen.refetch()} />;
  }
  const { planilla, totales, secciones } = resumen.data;
  return (
    <Screen scroll refreshing={resumen.isRefetching} onRefresh={() => void resumen.refetch()}>
      <Stack.Screen options={{ title: `Resumen · ${tituloPlanilla(planilla.fecha, planilla.hoja)}` }} />
      <TotalesPlanilla totales={totales} />
      <UsoSecciones secciones={secciones} hayLlenas={s.hayLlenas} onCrearSegunda={s.crearSegunda} />
      <Column gap="sm">
        <Button label="Abrir en Google Sheets" icon="externo" variant="outline" fullWidth onPress={s.abrirEnSheets} />
        <Button label="Corregir saldos desde aquí" icon="corregir_saldos" variant="ghost" fullWidth loading={s.corrigiendo} onPress={s.corregirSaldos} />
      </Column>
    </Screen>
  );
}
