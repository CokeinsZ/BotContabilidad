import type { ReactElement } from 'react';
import { RefreshControl, SectionList } from 'react-native';

import type { Trabajador } from '@/api/entities';
import { ListSeparator, SectionHeader } from '@/components/ui/lists';
import { colors } from '@/theme';
import type { SeccionTrabajadores } from '@/hooks/screens/trabajadores/useTrabajadoresScreen';

import { FilaTrabajador } from './FilaTrabajador';

interface ListaTrabajadoresProps {
  secciones: SeccionTrabajadores[];
  onAbrir: (trabajador: Trabajador) => void;
  refrescando: boolean;
  onRefrescar: () => void;
  encabezado: ReactElement;
  vacio: ReactElement;
}

export function ListaTrabajadores({ secciones, onAbrir, refrescando, onRefrescar, encabezado, vacio }: ListaTrabajadoresProps) {
  return (
    <SectionList
      sections={secciones}
      keyExtractor={(trabajador) => trabajador.id}
      ListHeaderComponent={encabezado}
      ListEmptyComponent={vacio}
      stickySectionHeadersEnabled
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="on-drag"
      renderSectionHeader={({ section }) => <SectionHeader title={section.title} />}
      renderItem={({ item }) => <FilaTrabajador trabajador={item} onPress={() => onAbrir(item)} />}
      ItemSeparatorComponent={ListSeparator}
      refreshControl={
        <RefreshControl refreshing={refrescando} onRefresh={onRefrescar} tintColor={colors.action.primary} colors={[colors.action.primary]} />
      }
      contentContainerStyle={{ paddingBottom: 48 }}
    />
  );
}
