/**
 * Fecha (texto) ⇄ calendario ⇄ hoja disponible.
 *
 * - Escribir una fecha válida o tocar un día mueve el calendario a su mes.
 * - Las hojas disponibles salen de las planillas que ya existen ese día.
 * - "Planilla secundaria" (hoja = 'siguiente') elige la hoja que sigue a la
 *   última del día, en cuanto se sabe cuál es; el usuario puede cambiarla.
 *
 * Todo se deriva en el render o se actualiza en el manejador del cambio:
 * nada de setState dentro de efectos.
 */
import { useMemo, useState } from 'react';

import { APP } from '@/constants/app';
import { usePlanillasDelMes } from '@/hooks/data/planillas/usePlanillasDelMes';
import { esFechaValida, mesDe, mismoMes, sumarDias, type MesAnio } from '@/utils/dates/fechaPlanilla';
import { opcionesHojas, origenSaldo, siguienteHoja } from '@/utils/planillas/disponibilidadHojas';

export function useFechaHojaSincronizadas(fechaInicial: string, hojaInicial: number | 'siguiente') {
  const [texto, setTexto] = useState(fechaInicial);
  const fecha = esFechaValida(texto) ? texto : null;
  const [mesVisible, setMesVisible] = useState<MesAnio>(() => mesDe(fechaInicial) ?? { anio: 2026, mes: 1 });
  // null = todavía no se eligió: se usa la hoja inicial (o la siguiente del día).
  const [hojaElegida, setHojaElegida] = useState<number | null>(typeof hojaInicial === 'number' ? hojaInicial : null);

  const mesFecha = fecha ? mesDe(fecha) : null;
  const fechaAnterior = fecha ? sumarDias(fecha, -1) : null;
  const mesAnterior = fechaAnterior ? mesDe(fechaAnterior) : null;
  const otroMesAnterior = !mismoMes(mesAnterior, mesFecha);

  const delMesVisible = usePlanillasDelMes(mesVisible);
  const delMesFecha = usePlanillasDelMes(mesFecha);
  const delMesAnterior = usePlanillasDelMes(mesAnterior, otroMesAnterior);

  const planillasFecha = useMemo(() => delMesFecha.data ?? [], [delMesFecha.data]);
  const hoja = hojaElegida ?? (fecha && delMesFecha.data ? siguienteHoja(fecha, planillasFecha) : 1);

  const planillasAlrededor = useMemo(
    () => [...planillasFecha, ...(otroMesAnterior ? (delMesAnterior.data ?? []) : [])],
    [planillasFecha, otroMesAnterior, delMesAnterior.data],
  );
  const opciones = useMemo(() => (fecha ? opcionesHojas(fecha, planillasFecha, APP.minSheetOptions) : []), [fecha, planillasFecha]);
  const marcas = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const planilla of delMesVisible.data ?? []) counts[planilla.fecha] = (counts[planilla.fecha] ?? 0) + 1;
    return counts;
  }, [delMesVisible.data]);

  const cambiarFecha = (nueva: string) => {
    setTexto(nueva);
    const mes = esFechaValida(nueva) ? mesDe(nueva) : null;
    if (mes && nueva !== fecha) {
      setMesVisible(mes);
      setHojaElegida(1);
    }
  };

  return {
    texto,
    fecha,
    errorFecha: texto.length === 10 && !fecha ? 'Esa fecha no existe. Usa dd-mm-aaaa.' : null,
    cambiarFecha,
    mesVisible,
    setMesVisible,
    marcas,
    hoja,
    setHoja: setHojaElegida,
    opciones,
    seleccion: opciones.find((opcion) => opcion.hoja === hoja) ?? null,
    fechaAnterior,
    origen: fecha ? origenSaldo(fecha, hoja, planillasAlrededor, fechaAnterior) : null,
    cargandoHojas: delMesFecha.isLoading || (otroMesAnterior && delMesAnterior.isLoading),
    errorHojas: delMesFecha.error,
  };
}
