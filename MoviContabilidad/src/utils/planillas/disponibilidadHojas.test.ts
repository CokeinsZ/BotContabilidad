import { opcionesHojas, origenSaldo, siguienteHoja, type PlanillaBasica } from './disponibilidadHojas';
import { nombreOrdinal, nombrePlanilla, tituloPlanilla } from './ordinales';

const planilla = (fecha: string, hoja: number): PlanillaBasica => ({
  id: `id-${fecha}-${hoja}`,
  nombre: nombrePlanilla(fecha, hoja),
  fecha,
  hoja,
});

describe('hojas de una fecha', () => {
  test('sin planillas: solo se puede crear la primera', () => {
    const opciones = opcionesHojas('24-11-2026', []);
    expect(opciones.map((o) => [o.etiqueta, o.existe, o.disponible])).toEqual([
      ['Primera', false, true],
      ['Segunda', false, false],
      ['Tercera', false, false],
    ]);
    expect(opciones[1].descripcion).toBe('Crea primero la primera');
    expect(siguienteHoja('24-11-2026', [])).toBe(1);
  });

  test('con la primera y la segunda: se abren y se puede crear la tercera', () => {
    const planillas = [planilla('24-11-2026', 1), planilla('24-11-2026', 2), planilla('23-11-2026', 1)];
    const opciones = opcionesHojas('24-11-2026', planillas);
    expect(opciones.map((o) => [o.hoja, o.existe, o.disponible])).toEqual([
      [1, true, true],
      [2, true, true],
      [3, false, true],
    ]);
    expect(opciones[0].planillaId).toBe('id-24-11-2026-1');
    expect(siguienteHoja('24-11-2026', planillas)).toBe(3);
  });

  test('si ya existen las tres aparece la cuarta', () => {
    const planillas = [1, 2, 3].map((hoja) => planilla('24-11-2026', hoja));
    const opciones = opcionesHojas('24-11-2026', planillas);
    expect(opciones).toHaveLength(4);
    expect(opciones[3]).toMatchObject({ hoja: 4, etiqueta: 'Cuarta', existe: false, disponible: true });
  });
});

describe('origen del saldo de caja', () => {
  const planillas = [planilla('23-11-2026', 1), planilla('23-11-2026', 2), planilla('24-11-2026', 1)];

  test('la primera hoja toma la hoja más alta del día anterior', () => {
    expect(origenSaldo('24-11-2026', 1, planillas, '23-11-2026')?.nombre).toBe('23-11-2026-2');
  });

  test('la hoja N toma la N-1 del mismo día', () => {
    expect(origenSaldo('24-11-2026', 2, planillas, '23-11-2026')?.nombre).toBe('24-11-2026');
  });

  test('sin planilla del día anterior no hay origen', () => {
    expect(origenSaldo('22-11-2026', 1, planillas, '21-11-2026')).toBeNull();
  });
});

test('nombres y títulos', () => {
  expect(nombreOrdinal(1)).toBe('Primera');
  expect(nombreOrdinal(11)).toBe('Hoja 11');
  expect(nombrePlanilla('24-11-2026', 2)).toBe('24-11-2026-2');
  expect(tituloPlanilla('24-11-2026', 2)).toBe('24-11-2026 · Hoja 2');
});
