import * as Clipboard from 'expo-clipboard';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useMemo } from 'react';

import { errorMessage, type Comando, type Mensaje, type OpcionSeleccion } from '@/api';
import { useAlert, useToast } from '@/components/ui/feedback';
import { APP } from '@/constants/app';
import { useComandos } from '@/hooks/data/comandos/useComandos';
import { puedeReintentarse, useEnviarMensaje } from '@/hooks/data/mensajes/useEnviarMensaje';
import { useEstadoChat } from '@/hooks/data/mensajes/useEstadoChat';
import { useHistorialChat } from '@/hooks/data/mensajes/useHistorialChat';
import { useSeleccion } from '@/hooks/data/mensajes/useSeleccion';
import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { usePlanilla } from '@/hooks/data/planillas/usePlanilla';
import { useTrabajadores } from '@/hooks/data/trabajadores/useTrabajadores';
import { vibrarEnvio, vibrarSeleccion } from '@/hooks/shared/haptics';
import { useAbrirEnGoogleSheets } from '@/hooks/shared/useAbrirEnGoogleSheets';
import { routes } from '@/navigation/routes';
import { abrirEnGoogleSheets } from '@/utils/linking/googleSheets';
import { sugerirTrabajadores } from '@/utils/planillas/sugerenciasTrabajador';

import { LIBRE } from './composer.reducer';
import { useComposer } from './useComposer';

export function useEdicionPlanillaScreen() {
  const params = useLocalSearchParams<{ planillaId: string; comando?: string; texto?: string }>();
  const planillaId = params.planillaId;
  const router = useRouter();
  const alert = useAlert();
  const toast = useToast();
  const abrirEnSheets = useAbrirEnGoogleSheets();

  const planilla = usePlanilla(planillaId);
  const perfil = usePerfil();
  const { comandos } = useComandos();
  const estado = useEstadoChat(planillaId);
  const historial = useHistorialChat(planillaId);
  const enviar = useEnviarMensaje(planillaId);
  const { responder, cancelar } = useSeleccion(planillaId);
  const composer = useComposer(
    comandos,
    params.comando ? { comandoId: params.comando, texto: params.texto ? `${params.texto} ` : '' } : null,
  );

  const sugiereTrabajador = composer.comando?.sugiereTrabajador ?? false;
  const trabajadores = useTrabajadores(sugiereTrabajador);
  const sugerencias = sugiereTrabajador
    ? sugerirTrabajadores(composer.texto, trabajadores.data?.trabajadores ?? [], APP.maxWorkerSuggestions)
    : [];

  const seleccion = estado.data?.seleccion ?? null;
  const deshacer = estado.data?.deshacer ?? null;
  const etiquetas = useMemo(() => new Map(comandos.map((comando) => [comando.id, comando.etiqueta])), [comandos]);

  const avisarError = useCallback((error: unknown) => toast.show(errorMessage(error), 'danger'), [toast]);

  const enviarComposer = () => {
    const envio = composer.tomarEnvio();
    if (!envio) return;
    vibrarEnvio();
    enviar.mutate(envio, { onError: avisarError });
  };

  const elegirComando = async (comando: Comando | typeof LIBRE) => {
    vibrarSeleccion();
    if (comando !== LIBRE && comando.argumentos === 'ninguno') {
      if (comando.confirmar) {
        const ok = await alert.confirmar({
          titulo: comando.id === 'deshacer' ? '¿Deshacer tu último mensaje?' : `¿${comando.etiqueta}?`,
          mensaje: comando.id === 'deshacer' && deshacer ? `Se revertirá: ${deshacer}.` : comando.ayuda,
          textoConfirmar: comando.etiqueta,
          destructiva: comando.id === 'deshacer',
        });
        if (!ok) return;
      }
      enviar.mutate({ comando: comando.id, texto: '' }, { onError: avisarError });
      return;
    }
    composer.seleccionar(comando === LIBRE ? LIBRE : comando.id);
  };

  const reintentar = async (mensaje: Mensaje) => {
    if (!mensaje.clientId) return;
    if (!puedeReintentarse(mensaje)) {
      await alert.mostrar({
        tipo: 'aviso',
        titulo: 'No sabemos si quedó registrado',
        mensaje: 'Pasó más de una hora. Revisa el resumen de la planilla antes de enviarlo de nuevo.',
      });
      return;
    }
    enviar.mutate({ comando: mensaje.comando, texto: mensaje.texto, clientId: mensaje.clientId }, { onError: avisarError });
  };

  const elegirOpcion = (opcion: OpcionSeleccion) => {
    vibrarSeleccion();
    responder.mutate(opcion, { onError: avisarError });
  };

  const cancelarPregunta = async () => {
    if (!seleccion) return;
    const ok = await alert.confirmar({
      titulo: 'Cancelar la pregunta',
      mensaje: `Se cancelará y se borrará de la planilla: ${seleccion.comando}.`,
      textoConfirmar: 'Sí, cancelar',
      destructiva: true,
    });
    if (ok) cancelar.mutate(undefined, { onError: avisarError });
  };

  return {
    planillaId,
    planilla: planilla.data ?? null,
    negocio: perfil.data?.negocio.nombre ?? '',
    googleConectado: perfil.data?.googleConectado ?? true,
    hoy: perfil.data?.hoy ?? '',
    comandos,
    etiquetas,
    historial,
    seleccion,
    deshacerDisponible: deshacer !== null,
    procesando: enviar.isPending || responder.isPending || cancelar.isPending,
    composer,
    sugerencias,
    enviarComposer,
    elegirComando,
    reintentar,
    elegirOpcion,
    cancelarPregunta,
    copiar: async (texto: string) => {
      await Clipboard.setStringAsync(texto);
      toast.show('Copiado');
    },
    abrirEnlace: (url: string) => void abrirEnGoogleSheets(url).catch(() => toast.show('No se pudo abrir el enlace.', 'danger')),
    crearSegundaPlanilla: () =>
      planilla.data && router.push(routes.nuevaPlanilla({ fecha: planilla.data.fecha, hoja: 'siguiente' })),
    verResumen: () => router.push(routes.resumenPlanilla(planillaId)),
    abrirEnSheets: () => planilla.data && abrirEnSheets(planilla.data.url),
  };
}
