import type {
  NominaDetalleDto,
  NominaRefDto,
  TrabajadorDetalleDto,
  TrabajadoresDto,
  ValeDto,
} from '../dto/trabajadores.dto';
import type { DetalleNomina, DetalleTrabajador, ListaTrabajadores, NominaRef, Vale } from '../entities';

function toVale(dto: ValeDto): Vale {
  return { fila: dto.fila, fecha: dto.fecha, monto: dto.monto, nota: dto.nota };
}

function toNominaRef(dto: NominaRefDto): NominaRef {
  return { hojaId: dto.hoja_id, titulo: dto.titulo, fecha: dto.fecha };
}

export function toListaTrabajadores(dto: TrabajadoresDto): ListaTrabajadores {
  return {
    carpetaConfigurada: dto.carpeta_configurada,
    trabajadores: dto.trabajadores.map((trabajador) => ({ ...trabajador })),
  };
}

export function toDetalleTrabajador(dto: TrabajadorDetalleDto): DetalleTrabajador {
  return {
    id: dto.id,
    nombre: dto.nombre,
    url: dto.url,
    totalPrestamos: dto.total_prestamos,
    vales: dto.vales.map(toVale),
    usados: dto.usados,
    capacidad: dto.capacidad,
    nominas: dto.nominas.map(toNominaRef),
  };
}

export function toDetalleNomina(dto: NominaDetalleDto): DetalleNomina {
  return {
    trabajador: { ...dto.trabajador },
    nomina: toNominaRef(dto.nomina),
    url: dto.url,
    totalPrestamos: dto.total_prestamos,
    vales: dto.vales.map(toVale),
  };
}
