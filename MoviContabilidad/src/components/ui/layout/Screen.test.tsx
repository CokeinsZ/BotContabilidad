import { render, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

import { Text } from '@/components/ui/typography';
import { TestProviders } from '@/test-utils/TestProviders';

import { Screen } from './Screen';

/** TestProviders usa un teléfono con zona segura de 47 arriba y 34 abajo. */
function paddingDelContenido() {
  // El ScrollView (ancestro del texto) recibe el estilo del contenido en `contentContainerStyle`.
  let nodo = screen.getByText('Hola').parent;
  while (nodo && nodo.props.contentContainerStyle === undefined) nodo = nodo.parent;
  const style = StyleSheet.flatten(nodo?.props.contentContainerStyle);
  return { top: style?.paddingTop, bottom: style?.paddingBottom };
}

test('el padding propio de la pantalla se suma a la zona segura, no la reemplaza', async () => {
  // Así estaba Vincular en el APK: el título quedaba bajo la barra de estado.
  await render(
    <Screen scroll edges={['top', 'bottom']} contentStyle={{ paddingTop: 32 }}>
      <Text>Hola</Text>
    </Screen>,
    { wrapper: TestProviders },
  );
  expect(paddingDelContenido()).toEqual({ top: 47 + 32, bottom: 34 + 24 });
});

test('sin padding propio: zona segura más el margen de siempre', async () => {
  await render(
    <Screen scroll edges={['top']}>
      <Text>Hola</Text>
    </Screen>,
    { wrapper: TestProviders },
  );
  expect(paddingDelContenido()).toEqual({ top: 47 + 16, bottom: 24 });
});
