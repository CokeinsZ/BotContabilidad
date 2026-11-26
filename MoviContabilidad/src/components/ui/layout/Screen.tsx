import type { ReactNode } from 'react';
import { RefreshControl, ScrollView, View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors, spacing } from '@/theme';

import { ScreenBackground, type ScreenBackgroundVariant } from '../backgrounds';
import { styles } from './Screen.styles';

export interface ScreenProps {
  children: ReactNode;
  /** Contenido con scroll (formularios, detalles). Las listas usan su propia FlatList. */
  scroll?: boolean;
  /** Margen lateral de 20. */
  padded?: boolean;
  /** Bordes con área segura. Con encabezado, el de arriba lo cubre el encabezado. */
  edges?: ('top' | 'bottom')[];
  background?: ScreenBackgroundVariant;
  watermark?: string;
  refreshing?: boolean;
  onRefresh?: () => void;
  /** Zona fija abajo (p. ej. el botón principal de un formulario). */
  footer?: ReactNode;
  contentStyle?: StyleProp<ViewStyle>;
}

/** Toda pantalla empieza con Screen: fondo, áreas seguras, margen y scroll/refresh opcionales. */
export function Screen({
  children,
  scroll = false,
  padded = true,
  edges = ['bottom'],
  background = 'plain',
  watermark,
  refreshing = false,
  onRefresh,
  footer,
  contentStyle,
}: ScreenProps) {
  const insets = useSafeAreaInsets();
  const top = edges.includes('top') ? insets.top : 0;
  const bottom = edges.includes('bottom') ? insets.bottom : 0;
  const body = scroll ? (
    <ScrollView
      style={styles.fill}
      contentContainerStyle={[
        styles.scrollContent,
        padded && styles.padded,
        { paddingTop: top + (padded ? spacing.lg : 0), paddingBottom: footer ? spacing.lg : bottom + spacing.xl },
        contentStyle,
      ]}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
      refreshControl={
        onRefresh ? (
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.action.primary}
            colors={[colors.action.primary]}
          />
        ) : undefined
      }
    >
      {children}
    </ScrollView>
  ) : (
    <View style={[styles.fill, padded && styles.padded, { paddingTop: top, paddingBottom: footer ? 0 : bottom }, contentStyle]}>
      {children}
    </View>
  );
  return (
    <ScreenBackground variant={background} watermark={watermark}>
      {body}
      {footer ? <View style={[styles.footer, { paddingBottom: bottom + spacing.md }]}>{footer}</View> : null}
    </ScreenBackground>
  );
}
