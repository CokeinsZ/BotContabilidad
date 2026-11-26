import { StyleSheet, View } from 'react-native';

import { errorMessage } from '@/api';
import { ScreenBackground } from '@/components/ui/backgrounds';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/feedback';
import { SearchField } from '@/components/ui/inputs';
import { Text } from '@/components/ui/typography';
import { spacing } from '@/theme';
import { useTrabajadoresScreen } from '@/hooks/screens/trabajadores/useTrabajadoresScreen';

import { ListaTrabajadores } from './ListaTrabajadores';

export default function TrabajadoresScreen() {
  const s = useTrabajadoresScreen();
  if (s.query.isLoading) return <LoadingState message="Leyendo la carpeta de trabajadores…" />;
  if (s.query.error && !s.query.data) {
    return <ErrorState message={errorMessage(s.query.error)} onRetry={() => void s.query.refetch()} />;
  }
  if (!s.carpetaConfigurada) {
    return (
      <EmptyState
        icon="carpeta"
        title="Sin carpeta de trabajadores"
        message="Este negocio no tiene carpeta de trabajadores en Drive. Pídesela al proveedor del bot."
      />
    );
  }
  return (
    <ScreenBackground>
      <ListaTrabajadores
        secciones={s.secciones}
        onAbrir={s.abrir}
        refrescando={s.query.isRefetching}
        onRefrescar={() => void s.query.refetch()}
        encabezado={
          <View style={styles.header}>
            <SearchField value={s.busqueda} onChange={s.setBusqueda} placeholder="Buscar trabajador" />
            <Text variant="caption">
              {s.busqueda ? `${s.encontrados} de ${s.total}` : `${s.total} trabajador${s.total === 1 ? '' : 'es'}`}
            </Text>
          </View>
        }
        vacio={
          s.total === 0 ? (
            <EmptyState
              icon="trabajadores"
              title="Todavía no hay trabajadores"
              message="El archivo de cada trabajador se crea solo al registrar su primer préstamo."
            />
          ) : (
            <EmptyState icon="buscar" title="Sin resultados" message={`Nadie coincide con «${s.busqueda}».`} compact />
          )
        }
      />
    </ScreenBackground>
  );
}

const styles = StyleSheet.create({
  header: { padding: spacing.gutter, paddingBottom: spacing.sm, gap: spacing.sm },
});
