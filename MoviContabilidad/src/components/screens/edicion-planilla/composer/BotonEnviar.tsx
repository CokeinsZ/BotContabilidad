import { IconButton } from '@/components/ui/buttons';

export function BotonEnviar({ onPress, disabled }: { onPress: () => void; disabled: boolean }) {
  return <IconButton icon="enviar" variant="primary" size={42} accessibilityLabel="Enviar" onPress={onPress} disabled={disabled} />;
}
