import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';

import { TapArea } from './TapArea';

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

async function renderFila() {
  const handlers = { onPress: jest.fn(), onDoubleTap: jest.fn(), onLongPress: jest.fn() };
  await render(
    <TapArea {...handlers} delayMs={260} accessibilityLabel="Planilla 24-11-2026">
      <Text>24-11-2026</Text>
    </TapArea>,
  );
  return handlers;
}

test('un toque espera por si llega el segundo y luego abre', async () => {
  const { onPress, onDoubleTap } = await renderFila();
  await fireEvent.press(screen.getByLabelText('Planilla 24-11-2026'));
  expect(onPress).not.toHaveBeenCalled();
  await act(async () => {
    jest.advanceTimersByTime(300);
  });
  expect(onPress).toHaveBeenCalledTimes(1);
  expect(onDoubleTap).not.toHaveBeenCalled();
});

test('dos toques seguidos son un doble toque (y no abren el chat)', async () => {
  const { onPress, onDoubleTap } = await renderFila();
  const fila = screen.getByLabelText('Planilla 24-11-2026');
  await fireEvent.press(fila);
  await fireEvent.press(fila);
  await act(async () => {
    jest.advanceTimersByTime(300);
  });
  expect(onDoubleTap).toHaveBeenCalledTimes(1);
  expect(onPress).not.toHaveBeenCalled();
});

test('mantener presionado abre las acciones', async () => {
  const { onLongPress } = await renderFila();
  await fireEvent(screen.getByLabelText('Planilla 24-11-2026'), 'longPress');
  expect(onLongPress).toHaveBeenCalledTimes(1);
});
