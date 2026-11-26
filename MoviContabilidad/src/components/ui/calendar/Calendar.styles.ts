import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const DAY_SIZE = 34;

export const styles = StyleSheet.create({
  container: {
    padding: spacing.md,
    paddingBottom: spacing.sm,
    borderRadius: radii.lg,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.screen,
    gap: spacing.xs,
  },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  week: { flexDirection: 'row' },
  weekday: { flex: 1, alignItems: 'center', paddingVertical: spacing.xs },
  day: { flex: 1, alignItems: 'center', height: DAY_SIZE + 12 },
  // El fondo base (igual al del calendario) no es decorativo: en Android, una
  // vista sin fondo ni borde se aplana, y al recibir el fondo de "seleccionado"
  // aparecía cuadrada (sin borderRadius). Con fondo desde el inicio, solo
  // cambia el color.
  dayCircle: {
    width: DAY_SIZE,
    height: DAY_SIZE,
    borderRadius: DAY_SIZE / 2,
    backgroundColor: colors.background.screen,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayPressed: { backgroundColor: colors.background.surface },
  daySelected: { backgroundColor: colors.action.primary },
  dayToday: { borderWidth: 2, borderColor: colors.decoration.gold },
  dots: { flexDirection: 'row', gap: 3, height: 6, marginTop: 2 },
  dot: { width: 4, height: 4, borderRadius: 2, backgroundColor: colors.decoration.goldIcon },
});
