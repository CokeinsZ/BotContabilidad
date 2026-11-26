export interface TrabajadorDto {
  id: string;
  nombre: string;
}

export interface TrabajadoresDto {
  carpeta_configurada: boolean;
  trabajadores: TrabajadorDto[];
}

export interface ValeDto {
  fila: number;
  fecha: string | null;
  monto: number | null;
  nota: string | null;
}

export interface NominaRefDto {
  hoja_id: number;
  titulo: string;
  fecha: string | null;
}

export interface TrabajadorDetalleDto {
  id: string;
  nombre: string;
  url: string;
  total_prestamos: number | null;
  vales: ValeDto[];
  usados: number;
  capacidad: number;
  nominas: NominaRefDto[];
}

export interface NominaDetalleDto {
  trabajador: TrabajadorDto;
  nomina: NominaRefDto;
  url: string;
  total_prestamos: number | null;
  vales: ValeDto[];
}
