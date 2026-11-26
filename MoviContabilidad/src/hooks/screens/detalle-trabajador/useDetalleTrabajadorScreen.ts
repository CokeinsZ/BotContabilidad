import { useLocalSearchParams, useRouter } from 'expo-router';

import type { NominaRef } from '@/api';
import { useAlert } from '@/components/ui/feedback';
import { usePlanillasDeHoy } from '@/hooks/data/planillas/usePlanillasDeHoy';
import { useTrabajador } from '@/hooks/data/trabajadores/useTrabajador';
import { useAbrirEnGoogleSheets } from '@/hooks/shared/useAbrirEnGoogleSheets';
import { routes } from '@/navigation/routes';

export function useDetalleTrabajadorScreen() {
  const { trabajadorId } = useLocalSearchParams<{ trabajadorId: string }>();
  const router = useRouter();
  const alert = useAlert();
  const abrirEnSheets = useAbrirEnGoogleSheets();
  const trabajador = useTrabajador(trabajadorId);
  const hoy = usePlanillasDeHoy();

  /** Préstamo y nómina se registran en una planilla: la última de hoy, con el comando ya elegido. */
  const irAlChatDeHoy = async (comando: 'trabajador' | 'nomina') => {
    const nombre = trabajador.data?.nombre;
    const ultima = hoy.data?.ultima;
    if (!nombre) return;
    if (ultima) {
      router.push(routes.planilla(ultima.id, { comando, texto: nombre }));
      return;
    }
    const crear = await alert.confirmar({
      titulo: 'Primero la planilla de hoy',
      mensaje: 'Los préstamos y la nómina se registran en la planilla del día. Créala y vuelve a intentarlo.',
      textoConfirmar: 'Crear planilla',
    });
    if (crear) router.push(routes.nuevaPlanilla({ fecha: hoy.data?.fecha }));
  };

  return {
    trabajador,
    prestar: () => void irAlChatDeHoy('trabajador'),
    pagarNomina: () => void irAlChatDeHoy('nomina'),
    abrirEnSheets: () => trabajador.data && abrirEnSheets(trabajador.data.url),
    abrirNomina: (nomina: NominaRef) => router.push(routes.nomina(trabajadorId, nomina.hojaId)),
  };
}
