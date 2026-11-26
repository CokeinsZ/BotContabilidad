import {
  compararFechas,
  esFechaValida,
  formatFecha,
  mesAnterior,
  mesDe,
  mesSiguiente,
  parseFecha,
  sumarDias,
} from './fechaPlanilla';

describe('fechas de planilla', () => {
  test('lee y escribe dd-mm-aaaa', () => {
    const date = parseFecha('24-11-2026');
    expect(date?.getFullYear()).toBe(2026);
    expect(date?.getMonth()).toBe(10);
    expect(date?.getDate()).toBe(24);
    expect(formatFecha(date!)).toBe('24-11-2026');
  });

  test('rechaza fechas que no existen o con otro formato', () => {
    expect(esFechaValida('31-02-2026')).toBe(false);
    expect(esFechaValida('2026-11-24')).toBe(false);
    expect(esFechaValida('24/11/2026')).toBe(false);
    expect(esFechaValida('29-02-2028')).toBe(true);
  });

  test('suma días cruzando meses y años', () => {
    expect(sumarDias('01-03-2026', -1)).toBe('28-02-2026');
    expect(sumarDias('31-12-2026', 1)).toBe('01-01-2027');
  });

  test('compara fechas por días', () => {
    expect(compararFechas('25-11-2026', '24-11-2026')).toBe(1);
    expect(compararFechas('24-11-2026', '24-11-2026')).toBe(0);
    expect(compararFechas('01-01-2026', '31-12-2025')).toBe(1);
  });

  test('meses anterior y siguiente', () => {
    expect(mesDe('24-11-2026')).toEqual({ anio: 2026, mes: 11 });
    expect(mesAnterior({ anio: 2026, mes: 1 })).toEqual({ anio: 2025, mes: 12 });
    expect(mesSiguiente({ anio: 2026, mes: 12 })).toEqual({ anio: 2027, mes: 1 });
  });
});
