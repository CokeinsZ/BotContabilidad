import { Card } from '@/components/ui/surfaces';
import { Text } from '@/components/ui/typography';

import { styles } from './VincularScreen.styles';

function formatoCuentaRegresiva(segundos: number): string {
  const minutos = Math.floor(segundos / 60);
  return `${minutos}:${String(segundos % 60).padStart(2, '0')}`;
}

/** El código en grande, enmarcado en dorado (por si se prefiere escribirlo a mano). */
export function CodigoVinculacion({ codigo, segundosRestantes }: { codigo: string; segundosRestantes: number }) {
  return (
    <Card variant="gold" style={styles.code} gap="xxs">
      <Text variant="code" accessibilityLabel={`Código ${codigo.split('').join(' ')}`} selectable>
        {`${codigo.slice(0, 3)} ${codigo.slice(3)}`}
      </Text>
      <Text variant="caption">Vence en {formatoCuentaRegresiva(segundosRestantes)}</Text>
    </Card>
  );
}
