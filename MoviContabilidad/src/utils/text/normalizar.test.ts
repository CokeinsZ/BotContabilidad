import { contiene, normalizar } from './normalizar';

test('normaliza como name_key del bot', () => {
  expect(normalizar('  MUÑOZ   Pérez ')).toBe('munoz perez');
  expect(normalizar('Chloë')).toBe('chloe');
  expect(contiene('María José', 'maria')).toBe(true);
  expect(contiene('Muñoz', 'munoz')).toBe(true);
  expect(contiene('pedro', 'maria')).toBe(false);
});
