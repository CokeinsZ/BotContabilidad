import { fireEvent, render, screen } from '@testing-library/react-native';

import { Calendar } from './Calendar';

test('marca hoy, el día elegido y las hojas que existen; tocar un día lo elige', async () => {
  const onSelect = jest.fn();
  const onMonthChange = jest.fn();
  await render(
    <Calendar
      month={{ anio: 2026, mes: 11 }}
      onMonthChange={onMonthChange}
      selected="24-11-2026"
      onSelect={onSelect}
      today="24-11-2026"
      marks={{ '24-11-2026': 2, '23-11-2026': 1 }}
    />,
  );
  expect(screen.getByText('Noviembre 2026')).toBeOnTheScreen();
  expect(screen.getByLabelText('24-11-2026, hoy, 2 planillas')).toBeSelected();
  expect(screen.getByLabelText('23-11-2026, 1 planilla')).not.toBeSelected();

  await fireEvent.press(screen.getByLabelText('25-11-2026'));
  expect(onSelect).toHaveBeenCalledWith('25-11-2026');

  await fireEvent.press(screen.getByLabelText('Mes siguiente'));
  expect(onMonthChange).toHaveBeenCalledWith({ anio: 2026, mes: 12 });
  await fireEvent.press(screen.getByLabelText('Mes anterior'));
  expect(onMonthChange).toHaveBeenCalledWith({ anio: 2026, mes: 10 });
});
