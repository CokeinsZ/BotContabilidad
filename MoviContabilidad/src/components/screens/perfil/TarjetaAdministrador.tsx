import type { Administrador } from '@/api/entities';
import { IconButton } from '@/components/ui/buttons';
import { Column, Row } from '@/components/ui/layout';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

export function TarjetaAdministrador({ administrador, onEditar }: { administrador: Administrador; onEditar: () => void }) {
  return (
    <Card>
      <Row justify="space-between">
        <Column gap="xxs" flex>
          <Text variant="overline">Administrador</Text>
          <Text variant="heading">{administrador.nombre}</Text>
        </Column>
        <IconButton icon="editar" variant="tonal" accessibilityLabel="Editar tu nombre" onPress={onEditar} />
      </Row>
      <Column gap="xxs">
        <Text variant="caption">Identificador de WhatsApp</Text>
        <Text variant="bodyStrong" selectable>
          {administrador.identificador}
        </Text>
        <Text variant="micro">Es tu identidad en el bot. Para cambiarlo, habla con el proveedor.</Text>
      </Column>
    </Card>
  );
}
