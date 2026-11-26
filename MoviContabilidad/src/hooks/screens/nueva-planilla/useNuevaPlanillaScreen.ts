import { useLocalSearchParams, useRouter } from 'expo-router';

import { errorMessage } from '@/api';
import { useAlert } from '@/components/ui/feedback';
import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { useCrearPlanilla } from '@/hooks/data/planillas/useCrearPlanilla';
import { routes } from '@/navigation/routes';
import { compararFechas, esFechaValida, formatFecha } from '@/utils/dates/fechaPlanilla';
import { nombreOrdinal } from '@/utils/planillas/ordinales';

import { useFechaHojaSincronizadas } from './useFechaHojaSincronizadas';

export function useNuevaPlanillaScreen() {
  const params = useLocalSearchParams<{ fecha?: string; hoja?: string }>();
  const router = useRouter();
  const alert = useAlert();
  const perfil = usePerfil();
  const crear = useCrearPlanilla();
  const hoy = perfil.data?.hoy ?? formatFecha(new Date());
  const fechaInicial = params.fecha && esFechaValida(params.fecha) ? params.fecha : hoy;
  const hojaInicial = params.hoja === 'siguiente' ? 'siguiente' : Math.max(1, Number(params.hoja) || 1);
  const sync = useFechaHojaSincronizadas(fechaInicial, hojaInicial);
  const accion: 'crear' | 'abrir' = sync.seleccion?.existe ? 'abrir' : 'crear';

  const enviar = async () => {
    const { fecha, seleccion } = sync;
    if (!fecha || !seleccion?.disponible) return;
    if (accion === 'crear' && compararFechas(fecha, hoy) > 0) {
      const seguir = await alert.confirmar({
        titulo: 'Fecha futura',
        mensaje: `Vas a crear la ${nombreOrdinal(seleccion.hoja).toLowerCase()} planilla del ${fecha}, que todavía no llega.`,
        textoConfirmar: 'Crear igual',
      });
      if (!seguir) return;
    }
    try {
      const apertura = await crear.mutateAsync({ fecha, hoja: seleccion.hoja });
      // replace: "atrás" vuelve a donde estaba el usuario, no al formulario.
      router.replace(routes.planilla(apertura.planilla.id));
    } catch (error) {
      await alert.mostrar({ tipo: 'error', titulo: 'No se pudo abrir la planilla', mensaje: errorMessage(error) });
    }
  };

  return {
    ...sync,
    hoy,
    accion,
    enviando: crear.isPending,
    puedeEnviar: !!sync.fecha && !!sync.seleccion?.disponible && !sync.cargandoHojas,
    enviar,
    errorHojas: sync.errorHojas ? errorMessage(sync.errorHojas) : null,
  };
}
