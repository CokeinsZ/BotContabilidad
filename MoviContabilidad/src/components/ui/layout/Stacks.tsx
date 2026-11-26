import type { PropsWithChildren } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';

import { spacing, type SpacingToken } from '@/theme';

interface StackProps {
  gap?: SpacingToken;
  align?: ViewStyle['alignItems'];
  justify?: ViewStyle['justifyContent'];
  wrap?: boolean;
  flex?: boolean;
  style?: StyleProp<ViewStyle>;
}

/** Fila con separación por token (nunca márgenes sueltos). */
export function Row({ gap = 'sm', align = 'center', justify, wrap, flex, style, children }: PropsWithChildren<StackProps>) {
  return (
    <View
      style={[
        { flexDirection: 'row', gap: spacing[gap], alignItems: align, justifyContent: justify },
        wrap && { flexWrap: 'wrap' },
        flex && { flex: 1 },
        style,
      ]}
    >
      {children}
    </View>
  );
}

/** Columna con separación por token. */
export function Column({ gap = 'sm', align, justify, flex, style, children }: PropsWithChildren<StackProps>) {
  return (
    <View style={[{ gap: spacing[gap], alignItems: align, justifyContent: justify }, flex && { flex: 1 }, style]}>
      {children}
    </View>
  );
}

/** Espacio fijo o flexible. */
export function Spacer({ size, flex }: { size?: SpacingToken; flex?: boolean }) {
  return <View style={flex ? { flex: 1 } : { height: spacing[size ?? 'md'], width: spacing[size ?? 'md'] }} />;
}
