import { MoneyText } from '@/components/domain/money';
import { Banner } from '@/components/ui/feedback';
import { ProgressBar } from '@/components/ui/progress';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

interface PeriodoActualProps {
  total: number | null;
  usados: number;
  capacidad: number;
}

export function PeriodoActual({ total, usados, capacidad }: PeriodoActualProps) {
  return (
    <Card>
      <Text variant="overline">Período actual</Text>
      <Text variant="caption">Total de préstamos</Text>
      <MoneyText value={total} variant="amountLarge" />
      <Text variant="captionStrong">{`${usados} de ${capacidad} vales usados`}</Text>
      <ProgressBar value={usados} max={capacidad} accessibilityLabel="Vales usados" />
      {usados >= capacidad ? (
        <Banner tone="warning" message="El archivo ya no tiene espacio para más vales: haz la nómina para cerrar el período." />
      ) : null}
    </Card>
  );
}
