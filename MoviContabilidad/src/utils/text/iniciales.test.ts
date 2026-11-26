import { iniciales } from './iniciales';

test('iniciales para monogramas y avatares', () => {
  expect(iniciales('Panadería La Espiga')).toBe('PE');
  expect(iniciales('juan')).toBe('J');
  expect(iniciales('maria jose perez')).toBe('MJ');
  expect(iniciales('La Espiga')).toBe('E');
  expect(iniciales('')).toBe('');
});
