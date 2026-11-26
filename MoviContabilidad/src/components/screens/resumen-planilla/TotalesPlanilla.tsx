import type { Totales } from '@/api/entities';
import { KpiGrid, KpiTile } from '@/components/domain/metrics';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

/** B38–B58 de la planilla. El saldo total, que pasa al día siguiente, en grande. */
export function TotalesPlanilla({ totales }: { totales: Totales }) {
  return (
    <Card>
      <Text variant="overline">Manejo del efectivo</Text>
      <KpiGrid
        columns={2}
        items={[
          { label: 'Gastos del día', value: totales.gastos },
          { label: 'Efectivo', value: totales.efectivo },
          { label: 'Venta total', value: totales.ventaTotal },
          { label: 'Saldo previo', value: totales.saldoPrevio },
        ]}
      />
      <KpiTile label="Saldo total (pasa a la siguiente planilla)" value={totales.saldoTotal} emphasis />
    </Card>
  );
}
