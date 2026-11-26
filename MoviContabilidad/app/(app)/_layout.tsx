import { Stack } from 'expo-router';

import { appScreens, appStackOptions } from '@/navigation';

export default function AppLayout() {
  return (
    <Stack screenOptions={appStackOptions}>
      {appScreens.map(({ name, options }) => (
        <Stack.Screen key={name} name={name} options={options} />
      ))}
    </Stack>
  );
}
