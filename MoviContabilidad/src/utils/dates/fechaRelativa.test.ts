import { diaCorto, etiquetaDia, fechaLarga, horaCorta } from './fechaRelativa';

test('fechas para mostrar', () => {
  expect(diaCorto('24-11-2026')).toBe('Mar 24 nov');
  expect(fechaLarga('24-11-2026')).toBe('martes 24 de noviembre');
});

test('separadores de día del chat', () => {
  const at = (d: number, h = 10) => new Date(2026, 10, d, h).getTime();
  expect(etiquetaDia(at(24), '24-11-2026')).toBe('Hoy');
  expect(etiquetaDia(at(23), '24-11-2026')).toBe('Ayer');
  expect(etiquetaDia(at(20), '24-11-2026')).toBe('vie 20 nov');
});

test('hora corta en formato de 12 horas', () => {
  expect(horaCorta(new Date(2026, 10, 24, 9, 5).getTime())).toBe('9:05 a. m.');
  expect(horaCorta(new Date(2026, 10, 24, 0, 30).getTime())).toBe('12:30 a. m.');
  expect(horaCorta(new Date(2026, 10, 24, 15, 0).getTime())).toBe('3:00 p. m.');
});
