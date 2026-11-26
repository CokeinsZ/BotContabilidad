import type { NominaRef } from '@/api/entities';
import { ListItem } from '@/components/ui/lists';
import { Section } from '@/components/ui/layout';
import { Text } from '@/components/ui/typography';
import { diaCorto } from '@/utils/dates/fechaRelativa';

/** Nóminas archivadas (cada una es una hoja del archivo del trabajador). */
export function ListaNominas({ nominas, onAbrir }: { nominas: NominaRef[]; onAbrir: (nomina: NominaRef) => void }) {
  return (
    <Section overline="Nóminas anteriores">
      {nominas.length === 0 ? (
        <Text tone="secondary">Todavía no tiene nóminas cerradas.</Text>
      ) : (
        nominas.map((nomina) => (
          <ListItem
            key={nomina.hojaId}
            title={nomina.fecha ? `Nómina del ${diaCorto(nomina.fecha)}` : nomina.titulo}
            subtitle={nomina.titulo}
            chevron
            onPress={() => onAbrir(nomina)}
            style={{ paddingHorizontal: 0 }}
          />
        ))
      )}
    </Section>
  );
}
