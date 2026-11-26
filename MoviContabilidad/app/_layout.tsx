import { RootStack } from '@/navigation';
import { AppProviders } from '@/providers';

export { ErrorBoundary } from 'expo-router';

export default function RootLayout() {
  return (
    <AppProviders>
      <RootStack />
    </AppProviders>
  );
}
