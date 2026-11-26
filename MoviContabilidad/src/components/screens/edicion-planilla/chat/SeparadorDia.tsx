import { View } from 'react-native';

import { Text } from '@/components/ui/typography';

import { styles } from './Chat.styles';

export function SeparadorDia({ etiqueta }: { etiqueta: string }) {
  return (
    <View style={styles.separator}>
      <Text variant="micro" tone="secondary">
        {etiqueta}
      </Text>
    </View>
  );
}
