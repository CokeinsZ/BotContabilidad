import type { PropsWithChildren } from 'react';
import { Pressable, View } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';

import { colors } from '@/theme';

import { Icon } from '../icons';
import { Text } from '../typography';
import { styles } from './Accordion.styles';

export interface AccordionProps {
  title: string;
  subtitle?: string;
  expanded: boolean;
  onToggle: () => void;
}

/** Lista desplegable (meses de Planillas). Controlado: el padre decide si está abierto. */
export function Accordion({ title, subtitle, expanded, onToggle, children }: PropsWithChildren<AccordionProps>) {
  return (
    <View style={styles.container}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={subtitle ? `${title}. ${subtitle}` : title}
        accessibilityState={{ expanded }}
        onPress={onToggle}
        style={({ pressed }) => [styles.header, pressed && styles.headerPressed]}
      >
        <View style={styles.texts}>
          <Text variant="heading">{title}</Text>
          {subtitle ? <Text variant="caption">{subtitle}</Text> : null}
        </View>
        <Icon name={expanded ? 'arriba' : 'abajo'} size="md" color={colors.text.secondary} />
      </Pressable>
      {expanded ? (
        <Animated.View entering={FadeIn.duration(160)} style={styles.content}>
          {children}
        </Animated.View>
      ) : null}
    </View>
  );
}
