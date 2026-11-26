import { semanasDelMes } from './calendario';

test('noviembre de 2026 empieza el domingo 1: la primera semana trae los días de octubre', () => {
  const weeks = semanasDelMes({ anio: 2026, mes: 11 });
  expect(weeks).toHaveLength(6);
  expect(weeks.every((week) => week.length === 7)).toBe(true);
  expect(weeks[0].map((day) => day.dia)).toEqual([26, 27, 28, 29, 30, 31, 1]);
  expect(weeks[0][6]).toEqual({ fecha: '01-11-2026', dia: 1, delMes: true });
  expect(weeks[0][0].delMes).toBe(false);
  expect(weeks[4].map((day) => day.dia)).toEqual([23, 24, 25, 26, 27, 28, 29]);
  expect(weeks[5][0]).toEqual({ fecha: '30-11-2026', dia: 30, delMes: true });
  expect(weeks[5][1]).toEqual({ fecha: '01-12-2026', dia: 1, delMes: false });
});
