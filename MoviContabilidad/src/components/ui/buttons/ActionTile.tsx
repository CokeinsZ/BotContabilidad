import { Pressable, View } from 'react-native';

import { colors } from '@/theme';

import { Icon, type IconName } from '../icons';
import { Text } from '../typography';
import { styles } from './ActionTile.styles';

export interface ActionTileProps {
  icon: IconName;
  title: string;
  subtitle?: string;
  onPress: () => void;
  /** featured = acción principal: relleno esmeralda con filete dorado. */
  variant?: 'default' | 'featured';
  /** Ocupa todo el ancho, en una fila, con flecha. */
  wide?: boolean;
}

/** Botón-tarjeta grande (grilla de la pantalla Principal). */
export function ActionTile({ icon, title, subtitle, onPress, variant = 'default', wide = false }: ActionTileProps) {
  const featured = variant === 'featured';
  const fg = featured ? colors.text.inverse : colors.action.primary;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={subtitle ? `${title}. ${subtitle}` : title}
      onPress={onPress}
      style={({ pressed }) => [
        styles.tile,
        wide && styles.wide,
        featured && styles.featured,
        pressed && (featured ? styles.featuredPressed : styles.pressed),
      ]}
    >
      <View style={[styles.iconBox, wide && styles.iconBoxWide, featured && styles.iconBoxFeatured]}>
        <Icon name={icon} size="md" color={fg} />
      </View>
      <View style={wide ? styles.texts : undefined}>
        <Text variant="bodyStrong" tone={featured ? 'inverse' : 'primary'}>{title}</Text>
        {subtitle ? (
          <Text variant="caption" style={featured ? { color: colors.text.inverseSoft } : undefined}>
            {subtitle}
          </Text>
        ) : null}
      </View>
      {wide ? <Icon name="derecha" size="md" color={colors.text.muted} /> : null}
    </Pressable>
  );
}
