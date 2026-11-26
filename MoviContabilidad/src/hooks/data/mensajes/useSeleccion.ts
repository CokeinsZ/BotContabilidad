/**
 * Responder o cancelar la pregunta pendiente del bot. En el historial queda,
 * como mensaje propio, lo que se eligió ("jose salon" / "Cancelar").
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { randomUUID } from 'expo-crypto';

import { cancelarSeleccion, responderSeleccion, type OpcionSeleccion } from '@/api';
import { useSession } from '@/session';
import { guardarMensajePropio, guardarRespuestas, marcarEstadoEnvio } from '@/storage';

import { queryKeys } from '../queryKeys';
import { afterChatResult } from './chatCache';

export function useSeleccion(planillaId: string) {
  const queryClient = useQueryClient();
  const { administradorId } = useSession();
  const adminId = administradorId ?? 0;

  const run = async (texto: string, call: () => ReturnType<typeof responderSeleccion>) => {
    const clientId = randomUUID();
    await guardarMensajePropio({ administradorId: adminId, planillaId, clientId, comando: null, texto });
    void queryClient.invalidateQueries({ queryKey: queryKeys.chat.historial(adminId, planillaId) });
    try {
      const result = await call();
      await guardarRespuestas(adminId, planillaId, clientId, result.respuestas);
      await marcarEstadoEnvio(clientId, 'enviado');
      afterChatResult(queryClient, adminId, planillaId, result);
      return result;
    } catch (error) {
      await marcarEstadoEnvio(clientId, 'fallido');
      void queryClient.invalidateQueries({ queryKey: queryKeys.chat.historial(adminId, planillaId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.chat.estado(planillaId) });
      throw error;
    }
  };

  const responder = useMutation({
    mutationFn: (opcion: OpcionSeleccion) => run(opcion.etiqueta, () => responderSeleccion(planillaId, opcion.valor)),
  });
  const cancelar = useMutation({
    mutationFn: () => run('Cancelar', () => cancelarSeleccion(planillaId)),
  });
  return { responder, cancelar };
}
