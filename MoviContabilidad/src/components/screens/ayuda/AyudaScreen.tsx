import { Column, Screen, Section } from '@/components/ui/layout';
import { Text } from '@/components/ui/typography';
import { useAyudaScreen } from '@/hooks/screens/ayuda/useAyudaScreen';

import { TarjetaComando } from './TarjetaComando';

const COMO_FUNCIONA = [
  ['El saldo pasa de un día al siguiente', 'Al crear una planilla, su saldo de caja se toma del saldo total de la anterior.'],
  ['Hojas adicionales en orden', 'La segunda hoja de un día toma el saldo de la primera. No hay tercera sin segunda.'],
  ['Deshacer', 'Revierte todo lo de tu último mensaje, aunque traiga varios movimientos.'],
  ['Trabajadores parecidos', 'Si hay varios con un nombre similar, el bot pregunta en cuál archivo guardar el vale.'],
  ['Secciones con límite', 'Cada sección tiene un número fijo de filas. Si una se llena, crea una planilla adicional del día.'],
  ['Historial en tu teléfono', 'El chat de cada planilla se guarda solo en este teléfono. Lo registrado está en Google Sheets.'],
] as const;

export default function AyudaScreen() {
  const { comandos } = useAyudaScreen();
  return (
    <Screen scroll>
      <Section overline="Comandos" title="Lo que puedes registrar">
        <Column gap="sm">
          {comandos.map((comando) => (
            <TarjetaComando key={comando.id} comando={comando} />
          ))}
        </Column>
      </Section>
      <Section overline="Cómo funciona">
        {COMO_FUNCIONA.map(([titulo, texto]) => (
          <Column key={titulo} gap="xxs">
            <Text variant="bodyStrong">{titulo}</Text>
            <Text tone="secondary">{texto}</Text>
          </Column>
        ))}
      </Section>
    </Screen>
  );
}
