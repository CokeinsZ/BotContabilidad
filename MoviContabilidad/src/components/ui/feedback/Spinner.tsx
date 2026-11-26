import { ActivityIndicator } from 'react-native';

import { colors } from '@/theme';

export function Spinner({ size = 'small', color = colors.action.primary }: { size?: 'small' | 'large'; color?: string }) {
  return <ActivityIndicator size={size} color={color} />;
}
