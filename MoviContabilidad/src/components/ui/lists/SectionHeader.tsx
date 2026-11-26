import { View } from 'react-native';

import { Text } from '../typography';
import { styles } from './ListItem.styles';

export function SectionHeader({ title }: { title: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text variant="overline" accessibilityRole="header">
        {title}
      </Text>
    </View>
  );
}
