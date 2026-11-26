import { fireEvent, render, screen } from '@testing-library/react-native';

import { COMANDOS_RESPALDO } from '@/constants/comandosRespaldo';

import { BandaComandos } from './BandaComandos';

test('la banda muestra "Libre" y los comandos; elegir uno avisa cuál', async () => {
  const onElegir = jest.fn();
  await render(
    <BandaComandos comandos={COMANDOS_RESPALDO} seleccionado="gasto" deshabilitada={false} deshacerDisponible={false} onElegir={onElegir} />,
  );
  expect(screen.getByRole('button', { name: 'Gasto' })).toBeSelected();
  expect(screen.getByRole('button', { name: 'Deshacer' })).toBeDisabled();

  await fireEvent.press(screen.getByRole('button', { name: 'Vale' }));
  expect(onElegir).toHaveBeenLastCalledWith(expect.objectContaining({ id: 'trabajador' }));
  await fireEvent.press(screen.getByRole('button', { name: 'Libre' }));
  expect(onElegir).toHaveBeenLastCalledWith('libre');
});

test('mientras el bot pregunta, la banda espera', async () => {
  await render(
    <BandaComandos comandos={COMANDOS_RESPALDO} seleccionado={null} deshabilitada deshacerDisponible onElegir={jest.fn()} />,
  );
  expect(screen.getByRole('button', { name: 'Gasto' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Libre' })).toBeDisabled();
});
