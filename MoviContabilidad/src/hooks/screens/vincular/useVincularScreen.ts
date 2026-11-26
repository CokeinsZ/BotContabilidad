import * as Clipboard from 'expo-clipboard';
import { useCallback, useEffect, useRef } from 'react';

import { errorMessage } from '@/api';
import { useAlert, useToast } from '@/components/ui/feedback';
import { useConsultaVinculacion } from '@/hooks/data/auth/useConsultaVinculacion';
import { useCrearVinculacion } from '@/hooks/data/auth/useCrearVinculacion';
import { useAhora } from '@/hooks/shared/useAhora';
import { useSession } from '@/session';
import { abrirUrl } from '@/utils/linking/externos';

export type FaseVinculacion = 'creando' | 'esperando' | 'vencida' | 'error';

/**
 * Vincular la app: pedir un código, abrir WhatsApp con "VINCULAR <código>" y
 * esperar a que el bot lo confirme. Al confirmarse, la sesión cambia y
 * `Stack.Protected` lleva sola a la pantalla Principal.
 */
export function useVincularScreen() {
  const session = useSession();
  const alert = useAlert();
  const toast = useToast();
  const crear = useCrearVinculacion();
  const vinculacion = crear.data ?? null;
  const ahora = useAhora(1000, vinculacion !== null);
  const vencidaLocal = vinculacion !== null && ahora >= vinculacion.venceEn;
  const consulta = useConsultaVinculacion(vinculacion?.id ?? null, vinculacion !== null && !vencidaLocal);
  const completando = useRef(false);
  const { mutate: generar, reset } = crear;

  useEffect(() => {
    generar();
  }, [generar]);

  useEffect(() => {
    const resultado = consulta.data;
    if (resultado?.estado === 'confirmada' && resultado.sesion && !completando.current) {
      completando.current = true;
      void session.completarVinculacion(resultado.sesion);
    }
  }, [consulta.data, session]);

  const estadoServidor = consulta.data?.estado;
  const fase: FaseVinculacion = crear.isPending
    ? 'creando'
    : crear.isError
      ? 'error'
      : vencidaLocal || estadoServidor === 'expirada' || estadoServidor === 'consumida'
        ? 'vencida'
        : 'esperando';

  const abrirWhatsApp = useCallback(async () => {
    if (!vinculacion) return;
    if (!vinculacion.whatsappUrl || !(await abrirUrl(vinculacion.whatsappUrl))) {
      await alert.mostrar({
        tipo: 'info',
        titulo: 'Envía el código por WhatsApp',
        mensaje: `Escríbele al bot este mensaje: ${vinculacion.mensaje}`,
      });
    }
  }, [alert, vinculacion]);

  const copiarMensaje = useCallback(async () => {
    if (!vinculacion) return;
    await Clipboard.setStringAsync(vinculacion.mensaje);
    toast.show('Mensaje copiado');
  }, [toast, vinculacion]);

  const generarOtro = useCallback(() => {
    completando.current = false;
    reset();
    generar();
  }, [generar, reset]);

  return {
    fase,
    vinculacion,
    segundosRestantes: vinculacion ? Math.max(0, Math.ceil((vinculacion.venceEn - ahora) / 1000)) : 0,
    error: crear.error ? errorMessage(crear.error) : null,
    abrirWhatsApp,
    copiarMensaje,
    generarOtro,
  };
}
