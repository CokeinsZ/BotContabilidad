import { Stack } from 'expo-router';

import { authStackOptions } from '@/navigation';

export default function AuthLayout() {
  return <Stack screenOptions={authStackOptions} />;
}
