/**
 * Historial del chat en la web (localStorage). Se importan los archivos `.web`
 * a propósito: Jest corre como teléfono y elegiría los de SQLite.
 */
import { APP } from '@/constants/app';

import { limpiarHistorialChat } from './chatHistory.cleanup.web';
import {
  borrarHistorial,
  guardarMensajePropio,
  guardarRespuestas,
  listarMensajes,
  marcarEstadoEnvio,
} from './chatHistory.repository.web';

const memoria = new Map<string, string>();
Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: {
    getItem: (clave: string) => memoria.get(clave) ?? null,
    setItem: (clave: string, valor: string) => void memoria.set(clave, valor),
    removeItem: (clave: string) => void memoria.delete(clave),
  },
});

const propio = (clientId: string, texto: string, planillaId = 'p1', administradorId = 7) => ({
  administradorId,
  planillaId,
  clientId,
  comando: 'gasto',
  texto,
});

beforeEach(() => memoria.clear());

test('guarda lo enviado y las respuestas, del más nuevo al más viejo', async () => {
  await guardarMensajePropio(propio('a', '5.000 pan'), 1000);
  await marcarEstadoEnvio('a', 'enviado');
  await guardarRespuestas(7, 'p1', 'a', [{ tipo: 'exito', texto: 'Gasto registrado: $5.000 - pan' }], 2000);

  const mensajes = await listarMensajes(7, 'p1', { limite: 10 });
  expect(mensajes.map((m) => [m.autor, m.texto, m.estadoEnvio, m.respondeA])).toEqual([
    ['bot', 'Gasto registrado: $5.000 - pan', null, 'a'],
    ['yo', '5.000 pan', 'enviado', null],
  ]);
});

test('pagina hacia atrás y separa por planilla y por administrador', async () => {
  for (const n of [1, 2, 3]) await guardarMensajePropio(propio(`c${n}`, `gasto ${n}`), n);
  await guardarMensajePropio(propio('otra', 'otra planilla', 'p2'), 4);
  await guardarMensajePropio(propio('ajeno', 'de otro admin', 'p1', 8), 5);

  const primera = await listarMensajes(7, 'p1', { limite: 2 });
  expect(primera.map((m) => m.texto)).toEqual(['gasto 3', 'gasto 2']);
  const segunda = await listarMensajes(7, 'p1', { antesDe: primera[1].id, limite: 2 });
  expect(segunda.map((m) => m.texto)).toEqual(['gasto 1']);

  await borrarHistorial(7);
  expect(await listarMensajes(7, 'p1', { limite: 10 })).toEqual([]);
  expect(await listarMensajes(8, 'p1', { limite: 10 })).toHaveLength(1);
});

test('un client_id repetido se rechaza, como el índice único de SQLite', async () => {
  await guardarMensajePropio(propio('a', 'uno'));
  await expect(guardarMensajePropio(propio('a', 'dos'))).rejects.toThrow('client_id repetido');
});

test('al abrir: lo que quedó "enviando" pasa a "fallido" y se borra lo de más de 90 días', async () => {
  const ahora = 10 * APP.chatRetentionMs;
  await guardarMensajePropio(propio('viejo', 'viejo'), ahora - APP.chatRetentionMs - 1);
  await guardarMensajePropio(propio('colgado', 'colgado'), ahora - 1000);

  await limpiarHistorialChat(ahora);

  const mensajes = await listarMensajes(7, 'p1', { limite: 10 });
  expect(mensajes.map((m) => [m.texto, m.estadoEnvio])).toEqual([['colgado', 'fallido']]);
});
