import type { Companero } from '@/api/entities';
import { Avatar } from '@/components/ui/avatars';
import { Badge } from '@/components/ui/badges';
import { ListItem } from '@/components/ui/lists';
import { Section } from '@/components/ui/layout';

/** Administradores del negocio (solo lectura: se dan de alta por la consola del bot). */
export function ListaAdministradores({ administradores }: { administradores: Companero[] }) {
  return (
    <Section overline="Administradores del negocio">
      {administradores.map((admin) => (
        <ListItem
          key={admin.id}
          title={admin.nombre}
          leading={<Avatar name={admin.nombre} size="sm" />}
          trailing={admin.esUsted ? <Badge label="Tú" tone="success" /> : undefined}
          style={{ paddingHorizontal: 0 }}
        />
      ))}
    </Section>
  );
}
