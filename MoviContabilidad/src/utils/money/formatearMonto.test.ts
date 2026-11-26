import { formatearMonto } from './formatearMonto';

test.each([
  [5000, '$5.000'],
  [1200000, '$1.200.000'],
  [0, '$0'],
  [999, '$999'],
  [2500.5, '$2.500,50'],
  [-3000, '-$3.000'],
  [null, '—'],
])('%p -> %s (igual que el bot)', (value, expected) => {
  expect(formatearMonto(value)).toBe(expected);
});
