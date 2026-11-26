import { aplicarMascaraFecha } from './mascaraFecha';

test.each([
  ['', ''],
  ['2', '2'],
  ['24', '24'],
  ['241', '24-1'],
  ['2411', '24-11'],
  ['24112026', '24-11-2026'],
  ['24-11-2026', '24-11-2026'],
  ['24/11/2026', '24-11-2026'],
  ['2411202699', '24-11-2026'],
])('máscara de "%s" -> "%s"', (input, expected) => {
  expect(aplicarMascaraFecha(input)).toBe(expected);
});
