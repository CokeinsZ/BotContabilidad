import { createRef } from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';

import type { TextInputRef } from '@/components/ui/inputs';

import { Composer } from './Composer';

async function renderComposer(texto: string, puedeEnviar: boolean) {
  const handlers = { onTexto: jest.fn(), onBorrarVacio: jest.fn(), onEnviar: jest.fn() };
  await render(
    <Composer
      inputRef={createRef<TextInputRef>()}
      etiqueta="Gasto"
      texto={texto}
      placeholder="Ej: 5.000 pan"
      puedeEnviar={puedeEnviar}
      {...handlers}
    />,
  );
  return handlers;
}

test('el comando va al inicio, en su propio elemento', async () => {
  await renderComposer('5.000 pan', true);
  // El prefijo es visual: el lector de pantalla ya dice "Mensaje de Gasto".
  expect(screen.getByText('Gasto:', { includeHiddenElements: true })).toBeOnTheScreen();
  expect(screen.getByLabelText('Mensaje de Gasto')).toHaveDisplayValue('5.000 pan');
});

test('borrar con el campo vacío quita el comando', async () => {
  const { onBorrarVacio } = await renderComposer('', false);
  await fireEvent(screen.getByLabelText('Mensaje de Gasto'), 'keyPress', { nativeEvent: { key: 'Backspace' } });
  expect(onBorrarVacio).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Enviar' })).toBeDisabled();
});

test('borrar con texto no quita el comando; enviar envía', async () => {
  const { onBorrarVacio, onEnviar } = await renderComposer('5.000', true);
  await fireEvent(screen.getByLabelText('Mensaje de Gasto'), 'keyPress', { nativeEvent: { key: 'Backspace' } });
  expect(onBorrarVacio).not.toHaveBeenCalled();
  await fireEvent.press(screen.getByRole('button', { name: 'Enviar' }));
  expect(onEnviar).toHaveBeenCalledTimes(1);
});
