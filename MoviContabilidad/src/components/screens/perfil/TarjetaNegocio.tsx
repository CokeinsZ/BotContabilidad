import type { Negocio } from '@/api/entities';
import { Button, IconButton } from '@/components/ui/buttons';
import { Column, Row } from '@/components/ui/layout';
import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

interface TarjetaNegocioProps {
  negocio: Negocio;
  onEditar: () => void;
  onCarpetaPlanillas: () => void;
  onCarpetaTrabajadores: () => void;
}

export function TarjetaNegocio({ negocio, onEditar, onCarpetaPlanillas, onCarpetaTrabajadores }: TarjetaNegocioProps) {
  return (
    <Card>
      <Row justify="space-between">
        <Column gap="xxs" flex>
          <Text variant="overline">Negocio</Text>
          <Text variant="heading">{negocio.nombre}</Text>
        </Column>
        <IconButton icon="editar" variant="tonal" accessibilityLabel="Editar el nombre del negocio" onPress={onEditar} />
      </Row>
      <Button label="Carpeta de planillas" icon="carpeta" variant="outline" size="sm" onPress={onCarpetaPlanillas} />
      {negocio.carpetaTrabajadoresUrl ? (
        <Button label="Carpeta de trabajadores" icon="trabajadores" variant="outline" size="sm" onPress={onCarpetaTrabajadores} />
      ) : (
        <Text variant="caption">Este negocio no tiene carpeta de trabajadores.</Text>
      )}
    </Card>
  );
}
