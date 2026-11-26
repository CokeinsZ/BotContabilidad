import type { Comando } from '@/api/entities';
import { Icon } from '@/components/ui/icons';
import { Column, Row } from '@/components/ui/layout';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

export function TarjetaComando({ comando }: { comando: Comando }) {
  return (
    <Card gap="sm">
      <Row gap="md">
        <Icon name={comando.icono} size="lg" color={colors.action.primary} />
        <Column gap="xxs" flex>
          <Text variant="bodyStrong">{comando.etiqueta}</Text>
          <Text variant="caption">{comando.ayuda}</Text>
        </Column>
      </Row>
      {comando.ejemplo ? (
        <Text variant="caption" tone="strong">
          Ejemplo: <Text variant="captionStrong" tone="action">{`${comando.etiqueta}: `}</Text>
          {comando.ejemplo}
        </Text>
      ) : null}
      {comando.alias.length ? <Text variant="micro">Por WhatsApp también: {[comando.id, ...comando.alias].join(', ')}</Text> : null}
    </Card>
  );
}
