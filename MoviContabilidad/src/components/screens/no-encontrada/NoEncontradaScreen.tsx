import { useRouter } from 'expo-router';

import { EmptyState } from '@/components/ui/feedback';
import { Screen } from '@/components/ui/layout';
import { routes } from '@/navigation/routes';

export default function NoEncontradaScreen() {
  const router = useRouter();
  return (
    <Screen edges={['top', 'bottom']} contentStyle={{ justifyContent: 'center' }}>
      <EmptyState
        icon="info"
        title="Esta pantalla no existe"
        message="El enlace que abriste no lleva a ninguna parte de la app."
        action={{ label: 'Volver al inicio', onPress: () => router.replace(routes.principal) }}
      />
    </Screen>
  );
}
