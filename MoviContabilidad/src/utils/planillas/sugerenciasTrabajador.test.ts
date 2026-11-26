import { completarNombre, parteNombre, sugerirTrabajadores } from './sugerenciasTrabajador';

const trabajadores = [{ nombre: 'María José' }, { nombre: 'mario' }, { nombre: 'pedro' }, { nombre: 'Muñoz' }];

test('sugiere por la parte del nombre, sin el monto', () => {
  expect(parteNombre('20.000 mari')).toBe('mari');
  expect(sugerirTrabajadores('20.000 mari', trabajadores).map((t) => t.nombre)).toEqual(['María José', 'mario']);
  expect(sugerirTrabajadores('5000 muno', trabajadores).map((t) => t.nombre)).toEqual(['Muñoz']);
  expect(sugerirTrabajadores('5000 munoz', trabajadores)).toEqual([]); // ya escrito: el bot ignora tildes
});

test('no sugiere con menos de dos letras ni repite el nombre exacto', () => {
  expect(sugerirTrabajadores('20000 m', trabajadores)).toEqual([]);
  expect(sugerirTrabajadores('20000 pedro', trabajadores)).toEqual([]);
});

test('completa el nombre conservando el monto', () => {
  expect(completarNombre('20.000 mari', 'maria jose')).toBe('20.000 maria jose');
  expect(completarNombre('mari', 'maria jose')).toBe('maria jose');
});
