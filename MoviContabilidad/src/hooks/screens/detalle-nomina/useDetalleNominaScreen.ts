import { useLocalSearchParams } from 'expo-router';

import { useNominaArchivada } from '@/hooks/data/trabajadores/useNominaArchivada';
import { useAbrirEnGoogleSheets } from '@/hooks/shared/useAbrirEnGoogleSheets';

export function useDetalleNominaScreen() {
  const { trabajadorId, nominaId } = useLocalSearchParams<{ trabajadorId: string; nominaId: string }>();
  const nomina = useNominaArchivada(trabajadorId, Number(nominaId));
  const abrirEnSheets = useAbrirEnGoogleSheets();
  return { nomina, abrirEnSheets: () => nomina.data && abrirEnSheets(nomina.data.url) };
}
