import { View } from 'react-native';

import { Text } from '../typography';
import { styles } from './Feedback.styles';
import { Spinner } from './Spinner';

export function LoadingState({ message = 'Cargando…' }: { message?: string }) {
  return (
    <View style={styles.state} accessibilityLiveRegion="polite">
      <Spinner size="large" />
      <Text tone="secondary">{message}</Text>
    </View>
  );
}
