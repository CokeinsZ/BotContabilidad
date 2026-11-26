import { useQueryClient } from '@tanstack/react-query';
import * as Clipboard from 'expo-clipboard';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';

import type { MesPlanillas, Planilla } from '@/api';
import { useToast } from '@/components/ui/feedback';
import { useMesesPlanillas } from '@/hooks/data/planillas/useMesesPlanillas';
import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { queryKeys } from '@/hooks/data/queryKeys';
import { useAbrirEnGoogleSheets } from '@/hooks/shared/useAbrirEnGoogleSheets';
import { routes } from '@/navigation/routes';
import { PREFERENCIAS, guardarPreferencia, leerPreferencia } from '@/storage';
import { mesDe } from '@/utils/dates/fechaPlanilla';
import { claveMes } from '@/utils/dates/meses';

export function usePlanillasScreen() {
  const router = useRouter();
  const toast = useToast();
  const queryClient = useQueryClient();
  const abrirEnSheets = useAbrirEnGoogleSheets();
  const meses = useMesesPlanillas();
  const perfil = usePerfil();
  const hoy = perfil.data?.hoy ?? null;
  const mesActual = hoy ? mesDe(hoy) : null;
  const claveActual = mesActual ? claveMes(mesActual.anio, mesActual.mes) : null;

  // El mes actual abierto por defecto (como la carpeta del mes en Drive); el
  // resto de meses, cerrados. Solo se guarda lo que el usuario cambió.
  const [elegidos, setElegidos] = useState<Record<string, boolean>>({});
  const estaAbierto = (mes: MesPlanillas) => {
    const clave = claveMes(mes.anio, mes.mes);
    return elegidos[clave] ?? clave === claveActual;
  };

  const [pistaVisible, setPistaVisible] = useState(false);
  useEffect(() => {
    void leerPreferencia(PREFERENCIAS.pistaDobleToqueVista).then((valor) => setPistaVisible(valor !== '1'));
  }, []);

  const [conAcciones, setConAcciones] = useState<Planilla | null>(null);
  const [refrescando, setRefrescando] = useState(false);

  const alternarMes = (mes: MesPlanillas) => {
    const clave = claveMes(mes.anio, mes.mes);
    setElegidos((actuales) => ({ ...actuales, [clave]: !(actuales[clave] ?? clave === claveActual) }));
  };

  const refrescar = useCallback(async () => {
    setRefrescando(true);
    await queryClient.invalidateQueries({ queryKey: queryKeys.planillas.all });
    setRefrescando(false);
  }, [queryClient]);

  return {
    meses,
    estaAbierto,
    alternarMes,
    pistaVisible,
    cerrarPista: () => {
      setPistaVisible(false);
      void guardarPreferencia(PREFERENCIAS.pistaDobleToqueVista, '1');
    },
    refrescando,
    refrescar,
    abrir: (planilla: Planilla) => router.push(routes.planilla(planilla.id)),
    abrirEnSheets: (planilla: Planilla) => abrirEnSheets(planilla.url),
    conAcciones,
    mostrarAcciones: setConAcciones,
    cerrarAcciones: () => setConAcciones(null),
    verResumen: (planilla: Planilla) => router.push(routes.resumenPlanilla(planilla.id)),
    copiarEnlace: async (planilla: Planilla) => {
      await Clipboard.setStringAsync(planilla.url);
      toast.show('Enlace copiado');
    },
    nueva: () => router.push(routes.nuevaPlanilla({ fecha: hoy ?? undefined })),
  };
}
