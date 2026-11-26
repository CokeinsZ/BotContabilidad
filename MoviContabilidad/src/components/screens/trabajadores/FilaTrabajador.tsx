import type { Trabajador } from '@/api/entities';
import { Avatar } from '@/components/ui/avatars';
import { ListItem } from '@/components/ui/lists';

export function FilaTrabajador({ trabajador, onPress }: { trabajador: Trabajador; onPress: () => void }) {
  return <ListItem title={trabajador.nombre} leading={<Avatar name={trabajador.nombre} size="sm" />} chevron onPress={onPress} />;
}
