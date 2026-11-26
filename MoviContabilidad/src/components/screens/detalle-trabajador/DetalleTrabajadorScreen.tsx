import { Stack } from 'expo-router';

import { errorMessage } from '@/api';
import { ErrorState, LoadingState } from '@/components/ui/feedback';
import { Screen } from '@/components/ui/layout';
import { useDetalleTrabajadorScreen } from '@/hooks/screens/detalle-trabajador/useDetalleTrabajadorScreen';

import { AccionesTrabajador } from './AccionesTrabajador';
import { EncabezadoTrabajador } from './EncabezadoTrabajador';
import { ListaNominas } from './ListaNominas';
import { ListaVales } from './ListaVales';
import { PeriodoActual } from './PeriodoActual';

export default function DetalleTrabajadorScreen() {
  const s = useDetalleTrabajadorScreen();
  const { trabajador } = s;
  if (trabajador.isLoading) return <LoadingState message="Leyendo el archivo del trabajador…" />;
  if (!trabajador.data) {
    return <ErrorState message={trabajador.error ? errorMessage(trabajador.error) : 'Sin datos.'} onRetry={() => void trabajador.refetch()} />;
  }
  const detalle = trabajador.data;
  return (
    <Screen scroll refreshing={trabajador.isRefetching} onRefresh={() => void trabajador.refetch()}>
      <Stack.Screen options={{ title: detalle.nombre }} />
      <EncabezadoTrabajador nombre={detalle.nombre} />
      <PeriodoActual total={detalle.totalPrestamos} usados={detalle.usados} capacidad={detalle.capacidad} />
      <AccionesTrabajador onPrestar={s.prestar} onPagarNomina={s.pagarNomina} onAbrirEnSheets={s.abrirEnSheets} />
      <ListaVales vales={detalle.vales} />
      <ListaNominas nominas={detalle.nominas} onAbrir={s.abrirNomina} />
    </Screen>
  );
}
