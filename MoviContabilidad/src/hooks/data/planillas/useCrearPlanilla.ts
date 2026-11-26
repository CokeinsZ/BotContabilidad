import { useMutation, useQueryClient } from '@tanstack/react-query';

import { crearOAbrirPlanilla } from '@/api';
import { useSession } from '@/session';
import { guardarRespuestas } from '@/storage';
import { mesDe } from '@/utils/dates/fechaPlanilla';

import { queryKeys } from '../queryKeys';

/**
 * Crea o abre una planilla con las reglas del bot. Los avisos del bot (p. ej.
 * "no hay planilla del día anterior") quedan como primeros mensajes del chat.
 */
export function useCrearPlanilla() {
  const queryClient = useQueryClient();
  const { administradorId } = useSession();
  return useMutation({
    mutationFn: ({ fecha, hoja }: { fecha: string; hoja: number }) => crearOAbrirPlanilla(fecha, hoja),
    onSuccess: async (apertura) => {
      const { planilla } = apertura;
      queryClient.setQueryData(queryKeys.planillas.detalle(planilla.id), planilla);
      if (administradorId !== null) {
        await guardarRespuestas(administradorId, planilla.id, null, apertura.mensajes).catch(() => undefined);
        void queryClient.invalidateQueries({ queryKey: queryKeys.chat.historial(administradorId, planilla.id) });
      }
      const mes = mesDe(planilla.fecha);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.planillas.meses }),
        queryClient.invalidateQueries({ queryKey: queryKeys.planillas.hoy }),
        mes ? queryClient.invalidateQueries({ queryKey: queryKeys.planillas.delMes(mes.anio, mes.mes) }) : null,
      ]);
    },
  });
}
