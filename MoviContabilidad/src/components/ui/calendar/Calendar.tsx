import { View } from 'react-native';

import { semanasDelMes } from '@/utils/dates/calendario';
import { mesAnterior, mesSiguiente } from '@/utils/dates/fechaPlanilla';

import { styles } from './Calendar.styles';
import type { CalendarProps } from './calendar.types';
import { CalendarDay } from './CalendarDay';
import { CalendarHeader } from './CalendarHeader';
import { CalendarWeekdays } from './CalendarWeekdays';

/** Calendario de un mes (semanas de lunes a domingo). La lógica está en utils/dates/calendario. */
export function Calendar({ month, onMonthChange, selected, onSelect, today, marks = {} }: CalendarProps) {
  const weeks = semanasDelMes(month);
  return (
    <View style={styles.container}>
      <CalendarHeader
        month={month}
        onPrevious={() => onMonthChange(mesAnterior(month))}
        onNext={() => onMonthChange(mesSiguiente(month))}
      />
      <CalendarWeekdays />
      {weeks.map((week) => (
        <View key={week[0].fecha} style={styles.week}>
          {week.map((day) => (
            <CalendarDay
              key={day.fecha}
              day={day}
              selected={day.fecha === selected}
              today={day.fecha === today}
              marks={marks[day.fecha] ?? 0}
              onPress={() => onSelect(day.fecha)}
            />
          ))}
        </View>
      ))}
    </View>
  );
}
