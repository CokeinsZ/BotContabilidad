import { View } from 'react-native';

import type { PlanillasDeHoy } from '@/api/entities';
import { KpiGrid } from '@/components/domain/metrics';
import { Badge } from '@/components/ui/badges';
import { Button } from '@/components/ui/buttons';
import { ErrorState, Skeleton } from '@/components/ui/feedback';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

import { styles } from './PrincipalScreen.styles';

interface TarjetaHoyProps {
  hoy: PlanillasDeHoy | undefined;
  cargando: boolean;
  error: string | null;
  creando: boolean;
  onContinuar: () => void;
  onCrearLaDeHoy: () => void;
  onElegirFecha: () => void;
  onReintentar: () => void;
}

/** Lo que más se usa cada día: seguir con la planilla de hoy o crearla con un toque. */
export function TarjetaHoy({ hoy, cargando, error, creando, onContinuar, onCrearLaDeHoy, onElegirFecha, onReintentar }: TarjetaHoyProps) {
  if (cargando && !hoy) {
    return (
      <Card>
        <View style={styles.skeleton}>
          <Skeleton width={120} height={12} />
          <Skeleton width={180} height={20} />
          <Skeleton height={44} />
        </View>
      </Card>
    );
  }
  if (error && !hoy) {
    return (
      <Card>
        <ErrorState compact message={error} onRetry={onReintentar} />
      </Card>
    );
  }
  if (!hoy) return null;
  const ultima = hoy.ultima;
  if (!ultima) {
    return (
      <Card>
        <Text variant="overline">Planilla de hoy</Text>
        <Text variant="heading">Aún no has creado la planilla de hoy</Text>
        <Button label="Crear la de hoy" icon="crearPlanilla" onPress={onCrearLaDeHoy} loading={creando} fullWidth />
        <Button label="Elegir otra fecha" variant="ghost" onPress={onElegirFecha} fullWidth />
      </Card>
    );
  }
  const totales = hoy.totales;
  return (
    <Card>
      <Text variant="overline">Planilla de hoy</Text>
      <View style={styles.todayTitle}>
        <Text variant="heading">{hoy.fecha}</Text>
        <Badge label={hoy.planillas.length === 1 ? '1 hoja' : `${hoy.planillas.length} hojas`} />
      </View>
      {totales ? (
        <KpiGrid
          items={[
            { label: 'Ventas', value: totales.ventaTotal },
            { label: 'Gastos', value: totales.gastos },
            { label: 'Saldo total', value: totales.saldoTotal },
          ]}
        />
      ) : null}
      <Button
        label={hoy.planillas.length > 1 ? `Continuar en Hoja ${ultima.hoja}` : 'Continuar'}
        icon="siguiente"
        iconPosition="right"
        onPress={onContinuar}
        fullWidth
      />
    </Card>
  );
}
