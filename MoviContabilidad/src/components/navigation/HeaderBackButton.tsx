import { IconButton } from '@/components/ui/buttons';

export function HeaderBackButton({ onPress }: { onPress: () => void }) {
  return <IconButton icon="atras" accessibilityLabel="Atrás" onPress={onPress} />;
}
