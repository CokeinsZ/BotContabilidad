import type { ReactElement } from 'react';
import { FlatList, RefreshControl } from 'react-native';

import type { MesPlanillas as Mes, Planilla } from '@/api/entities';
import { colors } from '@/theme';

import { MesPlanillas } from './MesPlanillas';
import { styles } from './PlanillasScreen.styles';

interface ListaMesesProps {
  meses: Mes[];
  estaAbierto: (mes: Mes) => boolean;
  onAlternar: (mes: Mes) => void;
  onAbrir: (planilla: Planilla) => void;
  onAbrirEnSheets: (planilla: Planilla) => void;
  onAcciones: (planilla: Planilla) => void;
  refrescando: boolean;
  onRefrescar: () => void;
  encabezado?: ReactElement | null;
  vacio?: ReactElement | null;
}

export function ListaMeses({ meses, estaAbierto, onAlternar, refrescando, onRefrescar, encabezado, vacio, ...acciones }: ListaMesesProps) {
  return (
    <FlatList
      data={meses}
      keyExtractor={(mes) => mes.carpeta}
      contentContainerStyle={styles.list}
      ListHeaderComponent={encabezado ?? undefined}
      ListEmptyComponent={vacio ?? undefined}
      renderItem={({ item }) => (
        <MesPlanillas mes={item} abierto={estaAbierto(item)} onAlternar={() => onAlternar(item)} {...acciones} />
      )}
      refreshControl={
        <RefreshControl refreshing={refrescando} onRefresh={onRefrescar} tintColor={colors.action.primary} colors={[colors.action.primary]} />
      }
    />
  );
}
