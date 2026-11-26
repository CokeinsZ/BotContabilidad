import { View } from 'react-native';

import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

import { styles } from './Composer.styles';

/** "Gasto:" al inicio del mensaje, en otro color. No es parte del texto: no se puede borrar letra a letra. */
export function PrefijoComando({ etiqueta }: { etiqueta: string }) {
  return (
    <View style={styles.prefix} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      <Text variant="bodyStrong" style={{ color: colors.chat.commandPrefix }}>
        {`${etiqueta}:`}
      </Text>
    </View>
  );
}
