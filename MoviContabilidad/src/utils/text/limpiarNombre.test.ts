import { limpiarNombre } from './limpiarNombre';

test('quita espacios de los extremos y deja uno solo entre palabras', () => {
  expect(limpiarNombre('  Panadería   La Espiga ')).toBe('Panadería La Espiga');
  expect(limpiarNombre('Admin\tde\nprueba')).toBe('Admin de prueba');
  expect(limpiarNombre('   ')).toBe('');
});
