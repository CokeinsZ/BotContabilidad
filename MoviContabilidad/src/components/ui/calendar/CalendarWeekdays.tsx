import { View } from 'react-native';

import { DIAS_SEMANA_CORTOS } from '@/utils/dates/calendario';

import { Text } from '../typography';
import { styles } from './Calendar.styles';

export function CalendarWeekdays() {
  return (
    <View style={styles.week} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
      {DIAS_SEMANA_CORTOS.map((day, index) => (
        <View key={index} style={styles.weekday}>
          <Text variant="captionStrong" tone="muted">
            {day}
          </Text>
        </View>
      ))}
    </View>
  );
}
