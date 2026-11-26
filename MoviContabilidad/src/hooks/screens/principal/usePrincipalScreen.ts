import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useCallback, useState } from 'react';

import { errorMessage } from '@/api';
import { useAlert } from '@/components/ui/feedback';
import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { queryKeys } from '@/hooks/data/queryKeys';
import { useCrearPlanilla } from '@/hooks/data/planillas/useCrearPlanilla';
import { usePlanillasDeHoy } from '@/hooks/data/planillas/usePlanillasDeHoy';
import { routes } from '@/navigation/routes';

export function usePrincipalScreen() {
  const router = useRouter();
  const alert = useAlert();
  const queryClient = useQueryClient();
  const perfil = usePerfil();
  const hoy = usePlanillasDeHoy();
  const crear = useCrearPlanilla();
  const [refrescando, setRefrescando] = useState(false);
  const fechaHoy = hoy.data?.fecha ?? perfil.data?.hoy ?? null;

  const crearLaDeHoy = useCallback(() => {
    if (!fechaHoy) return;
    crear.mutate(
      { fecha: fechaHoy, hoja: 1 },
      {
        onSuccess: (apertura) => router.push(routes.planilla(apertura.planilla.id)),
        onError: (error) =>
          void alert.mostrar({ tipo: 'error', titulo: 'No se pudo crear la planilla', mensaje: errorMessage(error) }),
      },
    );
  }, [alert, crear, fechaHoy, router]);

  const refrescar = useCallback(async () => {
    setRefrescando(true);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.perfil }),
      queryClient.invalidateQueries({ queryKey: queryKeys.planillas.hoy }),
    ]);
    setRefrescando(false);
  }, [queryClient]);

  const ultima = hoy.data?.ultima ?? null;
  const hojasHoy = hoy.data?.planillas.length ?? 0;

  return {
    perfil: perfil.data ?? null,
    fechaHoy,
    hoy,
    creando: crear.isPending,
    refrescando,
    refrescar,
    crearLaDeHoy,
    continuar: () => ultima && router.push(routes.planilla(ultima.id)),
    subtituloSecundaria: hojasHoy > 0 ? `Hoja ${hojasHoy + 1} de hoy` : 'Otra hoja del día',
    irA: {
      crearPlanilla: () => router.push(routes.nuevaPlanilla({ fecha: fechaHoy ?? undefined })),
      planillaSecundaria: () => router.push(routes.nuevaPlanilla({ fecha: fechaHoy ?? undefined, hoja: 'siguiente' })),
      planillas: () => router.push(routes.planillas),
      trabajadores: () => router.push(routes.trabajadores),
      perfil: () => router.push(routes.perfil),
      ayuda: () => router.push(routes.ayuda),
    },
  };
}
