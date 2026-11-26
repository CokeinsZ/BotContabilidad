/**
 * Enviar un mensaje del chat:
 * 1. Se guarda en el teléfono como "enviando" (aparece al instante).
 * 2. POST al bot con un client_id.
 * 3. Éxito: "enviado" + respuestas del bot guardadas. Error: "fallido".
 *
 * Reintentar usa el MISMO client_id: el bot no registra dos veces. El bot
 * recuerda cada client_id una hora; después, reintentar podría duplicar.
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { randomUUID } from 'expo-crypto';

import { enviarMensaje, type Mensaje } from '@/api';
import { APP } from '@/constants/app';
import { useSession } from '@/session';
import { guardarMensajePropio, guardarRespuestas, marcarEstadoEnvio } from '@/storage';

import { queryKeys } from '../queryKeys';
import { afterChatResult } from './chatCache';

interface Envio {
  comando: string | null;
  texto: string;
  /** Solo al reintentar un mensaje que falló. */
  clientId?: string;
}

export function puedeReintentarse(mensaje: Mensaje, ahora: number = Date.now()): boolean {
  return mensaje.autor === 'yo' && mensaje.estadoEnvio === 'fallido' && ahora - mensaje.creadoEn < APP.retryWindowMs;
}

export function useEnviarMensaje(planillaId: string) {
  const queryClient = useQueryClient();
  const { administradorId } = useSession();
  const adminId = administradorId ?? 0;
  const historial = queryKeys.chat.historial(adminId, planillaId);

  return useMutation({
    mutationFn: async ({ comando, texto, clientId }: Envio) => {
      const id = clientId ?? randomUUID();
      if (clientId) {
        await marcarEstadoEnvio(id, 'enviando');
      } else {
        await guardarMensajePropio({ administradorId: adminId, planillaId, clientId: id, comando, texto });
      }
      void queryClient.invalidateQueries({ queryKey: historial });
      try {
        const result = await enviarMensaje(planillaId, { clientId: id, comando, texto });
        await guardarRespuestas(adminId, planillaId, id, result.respuestas);
        await marcarEstadoEnvio(id, 'enviado');
        return result;
      } catch (error) {
        await marcarEstadoEnvio(id, 'fallido');
        void queryClient.invalidateQueries({ queryKey: historial });
        throw error;
      }
    },
    onSuccess: (result) => afterChatResult(queryClient, adminId, planillaId, result),
  });
}
