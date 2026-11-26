import { StyleSheet, View } from 'react-native';

import { Avatar } from '@/components/ui/avatars';
import { Text } from '@/components/ui/typography';
import { spacing } from '@/theme';

export function EncabezadoTrabajador({ nombre }: { nombre: string }) {
  return (
    <View style={styles.header}>
      <Avatar name={nombre} size="lg" variant="monogram" />
      <Text variant="title" accessibilityRole="header" style={styles.name}>
        {nombre}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  // Tal como está en Drive (y en la lista y el encabezado): sin capitalizar.
  name: { flex: 1 },
});
