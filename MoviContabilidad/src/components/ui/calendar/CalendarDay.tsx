import { Pressable, View } from 'react-native';

import type { DiaCalendario } from '@/utils/dates/calendario';

import { Text } from '../typography';
import { styles } from './Calendar.styles';

interface CalendarDayProps {
  day: DiaCalendario;
  selected: boolean;
  today: boolean;
  marks: number;
  onPress: () => void;
}

export function CalendarDay({ day, selected, today, marks, onPress }: CalendarDayProps) {
  const label = `${day.fecha}${today ? ', hoy' : ''}${marks ? `, ${marks} planilla${marks > 1 ? 's' : ''}` : ''}`;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ selected }}
      onPress={onPress}
      style={styles.day}
    >
      {({ pressed }) => (
        <>
          <View style={[styles.dayCircle, pressed && styles.dayPressed, today && styles.dayToday, selected && styles.daySelected]}>
            <Text
              variant={selected ? 'bodyStrong' : 'body'}
              tone={selected ? 'inverse' : day.delMes ? 'primary' : 'muted'}
              style={{ fontVariant: ['tabular-nums'] }}
            >
              {day.dia}
            </Text>
          </View>
          <View style={styles.dots}>
            {Array.from({ length: Math.min(marks, 3) }, (_, index) => (
              <View key={index} style={styles.dot} />
            ))}
          </View>
        </>
      )}
    </Pressable>
  );
}
