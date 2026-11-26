import { View } from 'react-native';

import { Avatar } from '@/components/ui/avatars';
import { IconButton } from '@/components/ui/buttons';
import { Text } from '@/components/ui/typography';
import { capitalizar } from '@/utils/dates/meses';
import { fechaLarga } from '@/utils/dates/fechaRelativa';

import { styles } from './PrincipalScreen.styles';

interface EncabezadoNegocioProps {
  negocio: string;
  administrador: string;
  fechaHoy: string | null;
  onAyuda: () => void;
}

export function EncabezadoNegocio({ negocio, administrador, fechaHoy, onAyuda }: EncabezadoNegocioProps) {
  return (
    <View style={styles.header}>
      <Avatar name={negocio} size="lg" variant="monogram" />
      <View style={styles.headerTexts}>
        <Text variant="display" numberOfLines={2} accessibilityRole="header">
          {negocio}
        </Text>
        <Text variant="caption">
          Hola, {administrador.split(' ')[0]}
          {fechaHoy ? ` · ${capitalizar(fechaLarga(fechaHoy))}` : ''}
        </Text>
      </View>
      <IconButton icon="ayuda" accessibilityLabel="Ayuda" onPress={onAyuda} />
    </View>
  );
}
