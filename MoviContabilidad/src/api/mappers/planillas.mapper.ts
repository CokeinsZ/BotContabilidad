import type { AbrirPlanillaDto, HoyDto, MesDto, PlanillaDto, ResumenDto, TotalesDto } from '../dto/planillas.dto';
import type { AperturaPlanilla, MesPlanillas, Planilla, PlanillasDeHoy, ResumenPlanilla, Totales } from '../entities';
import { toRespuesta } from './mensajes.mapper';

export function toPlanilla(dto: PlanillaDto): Planilla {
  return { id: dto.id, nombre: dto.nombre, fecha: dto.fecha, hoja: dto.hoja, url: dto.url };
}

export function toMes(dto: MesDto): MesPlanillas {
  return { anio: dto.anio, mes: dto.mes, carpeta: dto.carpeta, etiqueta: dto.etiqueta };
}

export function toTotales(dto: TotalesDto): Totales {
  return {
    gastos: dto.gastos,
    efectivo: dto.efectivo,
    ventaTotal: dto.venta_total,
    saldoPrevio: dto.saldo_previo,
    saldoTotal: dto.saldo_total,
  };
}

export function toPlanillasDeHoy(dto: HoyDto): PlanillasDeHoy {
  return {
    fecha: dto.fecha,
    planillas: dto.planillas.map(toPlanilla),
    ultima: dto.ultima ? toPlanilla(dto.ultima) : null,
    totales: dto.totales ? toTotales(dto.totales) : null,
  };
}

export function toResumen(dto: ResumenDto): ResumenPlanilla {
  return {
    planilla: toPlanilla(dto.planilla),
    totales: toTotales(dto.totales),
    secciones: dto.secciones.map((seccion) => ({ ...seccion })),
  };
}

export function toApertura(dto: AbrirPlanillaDto): AperturaPlanilla {
  return { planilla: toPlanilla(dto.planilla), creada: dto.creada, mensajes: dto.mensajes.map(toRespuesta) };
}
