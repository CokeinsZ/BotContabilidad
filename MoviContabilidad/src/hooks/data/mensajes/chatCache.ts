import type { QueryClient } from '@tanstack/react-query';

import type { ResultadoChat } from '@/api';

import { queryKeys } from '../queryKeys';

const COMANDOS_DE_TRABAJADORES = ['trabajador', 'nomina', 'retiro'];

/** Después de cada respuesta del bot: estado del chat, historial y lo que cambió en Sheets. */
export function afterChatResult(
  queryClient: QueryClient,
  administradorId: number,
  planillaId: string,
  result: ResultadoChat,
): void {
  queryClient.setQueryData(queryKeys.chat.estado(planillaId), result.estado);
  void queryClient.invalidateQueries({ queryKey: queryKeys.chat.historial(administradorId, planillaId) });
  void queryClient.invalidateQueries({ queryKey: queryKeys.planillas.resumen(planillaId) });
  void queryClient.invalidateQueries({ queryKey: queryKeys.planillas.hoy });
  const tocaTrabajadores =
    result.comandos.some((comando) => COMANDOS_DE_TRABAJADORES.includes(comando.split(' ')[0])) ||
    result.respuestas.some((respuesta) => respuesta.tipo === 'seleccion');
  if (tocaTrabajadores) void queryClient.invalidateQueries({ queryKey: queryKeys.trabajadores.all });
}
