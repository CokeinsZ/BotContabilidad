import { LIBRE, composerInicial, composerReducer, envioDe, type ComposerState } from './composer.reducer';

const run = (...actions: Parameters<typeof composerReducer>[1][]): ComposerState =>
  actions.reduce(composerReducer, composerInicial);

test('elegir un comando abre el composer con su prefijo', () => {
  expect(run({ type: 'seleccionar', comandoId: 'gasto' })).toEqual({ comandoId: 'gasto', texto: '' });
});

test('sin comando no se puede escribir', () => {
  expect(run({ type: 'escribir', texto: 'hola' })).toEqual(composerInicial);
});

test('cambiar de comando conserva el texto; tocar el mismo lo quita', () => {
  const cambiado = run({ type: 'seleccionar', comandoId: 'gasto' }, { type: 'escribir', texto: '5.000 pan' }, { type: 'seleccionar', comandoId: 'retiro' });
  expect(cambiado).toEqual({ comandoId: 'retiro', texto: '5.000 pan' });
  expect(composerReducer(cambiado, { type: 'seleccionar', comandoId: 'retiro' })).toEqual(composerInicial);
});

test('al enviar el comando sigue elegido (modo ráfaga) y el texto se limpia', () => {
  const enviado = run({ type: 'seleccionar', comandoId: 'gasto' }, { type: 'escribir', texto: '5.000 pan' }, { type: 'enviado' });
  expect(enviado).toEqual({ comandoId: 'gasto', texto: '' });
});

test('lo que se envía al bot', () => {
  expect(envioDe({ comandoId: 'gasto', texto: '  5.000   pan ' })).toEqual({ comando: 'gasto', texto: '5.000 pan' });
  expect(envioDe({ comandoId: LIBRE, texto: 'gasto 5000 pan y 3000 leche' })).toEqual({ comando: null, texto: 'gasto 5000 pan y 3000 leche' });
  expect(envioDe({ comandoId: 'gasto', texto: '   ' })).toBeNull();
  expect(envioDe(composerInicial)).toBeNull();
});
