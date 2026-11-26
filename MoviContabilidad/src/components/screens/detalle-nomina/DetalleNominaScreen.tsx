import { Stack } from 'expo-router';

import { errorMessage } from '@/api';
import { MoneyText } from '@/components/domain/money';
import { ValeRow } from '@/components/domain/trabajadores';
import { Button } from '@/components/ui/buttons';
import { ErrorState, LoadingState } from '@/components/ui/feedback';
import { Screen, Section } from '@/components/ui/layout';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';
import { useDetalleNominaScreen } from '@/hooks/screens/detalle-nomina/useDetalleNominaScreen';
import { diaCorto } from '@/utils/dates/fechaRelativa';

export default function DetalleNominaScreen() {
  const { nomina, abrirEnSheets } = useDetalleNominaScreen();
  if (nomina.isLoading) return <LoadingState message="Leyendo la nómina…" />;
  if (!nomina.data) {
    return <ErrorState message={nomina.error ? errorMessage(nomina.error) : 'Sin datos.'} onRetry={() => void nomina.refetch()} />;
  }
  const detalle = nomina.data;
  const fecha = detalle.nomina.fecha ? diaCorto(detalle.nomina.fecha) : detalle.nomina.titulo;
  return (
    <Screen scroll>
      <Stack.Screen options={{ title: `Nómina · ${fecha}` }} />
      <Card>
        <Text variant="overline">{detalle.trabajador.nombre}</Text>
        <Text variant="caption">Total de vales del período</Text>
        <MoneyText value={detalle.totalPrestamos} variant="amountLarge" />
      </Card>
      <Section overline="Vales del período">
        {detalle.vales.length === 0 ? (
          <Text tone="secondary">Ese período no tenía vales.</Text>
        ) : (
          detalle.vales.map((vale) => <ValeRow key={vale.fila} vale={vale} />)
        )}
      </Section>
      <Button label="Abrir en Google Sheets" icon="externo" variant="outline" fullWidth onPress={abrirEnSheets} />
    </Screen>
  );
}
