import { useLocalSearchParams, useRouter } from 'expo-router';

import { errorMessage } from '@/api';
import { useAlert } from '@/components/ui/feedback';
import { useEnviarMensaje } from '@/hooks/data/mensajes/useEnviarMensaje';
import { useResumenPlanilla } from '@/hooks/data/planillas/useResumenPlanilla';
import { useAbrirEnGoogleSheets } from '@/hooks/shared/useAbrirEnGoogleSheets';
import { routes } from '@/navigation/routes';

export function useResumenPlanillaScreen() {
  const { planillaId } = useLocalSearchParams<{ planillaId: string }>();
  const router = useRouter();
  const alert = useAlert();
  const abrirEnSheets = useAbrirEnGoogleSheets();
  const resumen = useResumenPlanilla(planillaId);
  const enviar = useEnviarMensaje(planillaId);
  const planilla = resumen.data?.planilla ?? null;
  const hayLlenas = (resumen.data?.secciones ?? []).some((seccion) => seccion.usadas !== null && seccion.usadas >= seccion.capacidad);

  /** Igual que el comando del chat: queda en el historial de la planilla. */
  const corregirSaldos = async () => {
    const ok = await alert.confirmar({
      titulo: 'Corregir saldos desde aquí',
      mensaje: 'Recalcula el saldo de caja de todas las planillas siguientes a esta, en orden. Se puede deshacer desde el chat.',
      textoConfirmar: 'Corregir',
    });
    if (!ok) return;
    try {
      const result = await enviar.mutateAsync({ comando: 'corregir_saldos', texto: '' });
      await alert.mostrar({
        tipo: result.respuestas.some((r) => r.tipo === 'error' || r.tipo === 'aviso') ? 'aviso' : 'exito',
        titulo: 'Saldos',
        mensaje: result.respuestas.map((r) => r.texto).join('\n'),
      });
      void resumen.refetch();
    } catch (error) {
      await alert.mostrar({ tipo: 'error', titulo: 'No se pudieron corregir los saldos', mensaje: errorMessage(error) });
    }
  };

  return {
    resumen,
    planilla,
    hayLlenas,
    corrigiendo: enviar.isPending,
    corregirSaldos,
    abrirEnSheets: () => planilla && abrirEnSheets(planilla.url),
    crearSegunda: () => planilla && router.push(routes.nuevaPlanilla({ fecha: planilla.fecha, hoja: 'siguiente' })),
  };
}
