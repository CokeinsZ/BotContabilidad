import { fireEvent, render, screen } from '@testing-library/react-native';

import { TestProviders } from '@/test-utils/TestProviders';

import { Dropdown } from './Dropdown';

const options = [
  { value: 1, label: 'Primera', description: 'Ya existe: se abrirá' },
  { value: 2, label: 'Segunda' },
  { value: 3, label: 'Tercera', description: 'Crea primero la segunda', disabled: true },
];

test('elige una opción y no deja elegir una deshabilitada', async () => {
  const onChange = jest.fn();
  await render(<Dropdown label="Hoja" value={1} options={options} onChange={onChange} />, { wrapper: TestProviders });
  await fireEvent.press(screen.getByLabelText('Hoja: Primera'));

  expect(screen.getByLabelText('Tercera. Crea primero la segunda')).toBeDisabled();
  await fireEvent.press(screen.getByLabelText('Tercera. Crea primero la segunda'));
  expect(onChange).not.toHaveBeenCalled();

  await fireEvent.press(screen.getByLabelText('Segunda'));
  expect(onChange).toHaveBeenCalledWith(2);
});
