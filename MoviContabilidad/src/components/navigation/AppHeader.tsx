/**
 * Encabezado de todas las pantallas de la app: atrás, título (o el
 * `headerTitle` propio de la pantalla), acciones a la derecha y el filete
 * dorado de 1 px. Lo conecta `appStackOptions.header`.
 */
import type { NativeStackHeaderProps } from 'expo-router';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { GoldDivider } from '@/components/ui/decorations';
import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

import { styles } from './AppHeader.styles';
import { HeaderBackButton } from './HeaderBackButton';

export function AppHeader({ navigation, options, route, back }: NativeStackHeaderProps) {
  const insets = useSafeAreaInsets();
  const title = typeof options.headerTitle === 'string' ? options.headerTitle : (options.title ?? route.name);
  const titleNode =
    typeof options.headerTitle === 'function' ? (
      options.headerTitle({ children: title, tintColor: colors.text.primary })
    ) : (
      <Text variant="heading" numberOfLines={1} accessibilityRole="header">
        {title}
      </Text>
    );
  const right = options.headerRight?.({ tintColor: colors.text.primary, canGoBack: !!back });
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.bar}>
        <View style={styles.side}>{back ? <HeaderBackButton onPress={navigation.goBack} /> : null}</View>
        <View style={styles.title}>{titleNode}</View>
        <View style={styles.right}>{right}</View>
      </View>
      <GoldDivider />
    </View>
  );
}
