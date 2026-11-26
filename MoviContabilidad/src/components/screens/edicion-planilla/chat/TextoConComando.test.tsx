import { render, screen } from '@testing-library/react-native';

import { TextoConComando } from './TextoConComando';

test('con texto: "Comando: texto"', async () => {
  await render(<TextoConComando etiqueta="Gasto" texto="5.000 pan" />);
  expect(screen.getByText('Gasto: 5.000 pan')).toBeOnTheScreen();
});

test('sin texto (Deshacer, Terminar día): solo el comando, sin dos puntos', async () => {
  await render(<TextoConComando etiqueta="Deshacer" texto="" />);
  expect(screen.queryByText(/:/)).toBeNull();
  expect(screen.getAllByText('Deshacer').length).toBeGreaterThan(0);
});

test('mensaje libre: solo el texto', async () => {
  await render(<TextoConComando etiqueta={null} texto="5 mil de pan" />);
  expect(screen.getByText('5 mil de pan')).toBeOnTheScreen();
});
