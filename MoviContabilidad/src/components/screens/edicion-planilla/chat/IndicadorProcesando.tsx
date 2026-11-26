import { View } from 'react-native';

import { Spinner } from '@/components/ui/feedback';
import { Text } from '@/components/ui/typography';

import { styles } from './Chat.styles';

/** Mientras el bot responde (DeepSeek y Google pueden tardar). */
export function IndicadorProcesando() {
  return (
    <View style={styles.processing} accessibilityLiveRegion="polite">
      <Spinner />
      <Text variant="caption">Registrando…</Text>
    </View>
  );
}
