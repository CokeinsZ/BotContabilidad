import { toVinculacion } from './auth.mapper';
import { toEstadoChat, toResultadoChat } from './mensajes.mapper';
import { toPlanillasDeHoy } from './planillas.mapper';
import { toDetalleTrabajador } from './trabajadores.mapper';

test('vinculación: calcula cuándo vence el código', () => {
  const vinculacion = toVinculacion(
    { vinculacion_id: 'abc', codigo: '482913', mensaje: 'VINCULAR 482913', whatsapp_url: null, expira_en: 300 },
    1_000,
  );
  expect(vinculacion).toEqual({ id: 'abc', codigo: '482913', mensaje: 'VINCULAR 482913', whatsappUrl: null, venceEn: 301_000 });
});

test('resultado del chat con pregunta pendiente', () => {
  const resultado = toResultadoChat({
    client_id: 'c1',
    comandos: ['trabajador 20000 jose'],
    interpretado_por_ia: false,
    respuestas: [{ tipo: 'exito', texto: 'Préstamo registrado' }, { tipo: 'seleccion', texto: '¿Cuál?' }],
    estado: {
      seleccion: {
        pregunta: '¿Cuál?',
        opciones: [{ valor: 1, etiqueta: 'jose salon', crea: false }],
        comando: 'trabajador 20000 jose',
        planilla_id: 'p1',
        planilla_nombre: '24-11-2026',
      },
      deshacer: 'trabajador 20000 jose',
    },
    procesado_en: '2026-11-24T15:02:13-05:00',
  });
  expect(resultado.estado.seleccion).toEqual({
    pregunta: '¿Cuál?',
    opciones: [{ valor: 1, etiqueta: 'jose salon', crea: false }],
    comando: 'trabajador 20000 jose',
    planillaId: 'p1',
    planillaNombre: '24-11-2026',
  });
  expect(resultado.interpretadoPorIa).toBe(false);
  expect(toEstadoChat({ seleccion: null, deshacer: null })).toEqual({ seleccion: null, deshacer: null });
});

test('planillas de hoy y trabajador a camelCase', () => {
  const hoy = toPlanillasDeHoy({
    fecha: '24-11-2026',
    planillas: [{ id: 'p1', nombre: '24-11-2026', fecha: '24-11-2026', hoja: 1, url: 'u' }],
    ultima: { id: 'p1', nombre: '24-11-2026', fecha: '24-11-2026', hoja: 1, url: 'u' },
    totales: { gastos: 1, efectivo: 2, venta_total: 3, saldo_previo: 4, saldo_total: 5 },
  });
  expect(hoy.totales).toEqual({ gastos: 1, efectivo: 2, ventaTotal: 3, saldoPrevio: 4, saldoTotal: 5 });

  const detalle = toDetalleTrabajador({
    id: 't1', nombre: 'juan', url: 'u', total_prestamos: 25000, usados: 2, capacidad: 16,
    vales: [{ fila: 13, fecha: '24-11-2026', monto: 20000, nota: null }],
    nominas: [{ hoja_id: 9, titulo: '24-11-2026', fecha: '24-11-2026' }],
  });
  expect(detalle.totalPrestamos).toBe(25000);
  expect(detalle.nominas).toEqual([{ hojaId: 9, titulo: '24-11-2026', fecha: '24-11-2026' }]);
});
