import type { Vale } from '@/api/entities';
import { ValeRow } from '@/components/domain/trabajadores';
import { Section } from '@/components/ui/layout';
import { Text } from '@/components/ui/typography';

/** Vales del período, del más reciente al más antiguo. */
export function ListaVales({ vales }: { vales: Vale[] }) {
  const ordenados = [...vales].reverse();
  return (
    <Section overline="Vales" title={vales.length ? `${vales.length} préstamo${vales.length === 1 ? '' : 's'}` : undefined}>
      {ordenados.length === 0 ? (
        <Text tone="secondary">No tiene préstamos en este período.</Text>
      ) : (
        ordenados.map((vale) => <ValeRow key={vale.fila} vale={vale} />)
      )}
    </Section>
  );
}
