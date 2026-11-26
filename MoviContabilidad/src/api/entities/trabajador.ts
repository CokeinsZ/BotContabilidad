export interface Trabajador {
  id: string;
  nombre: string;
}

export interface ListaTrabajadores {
  carpetaConfigurada: boolean;
  trabajadores: Trabajador[];
}

export interface Vale {
  fila: number;
  fecha: string | null;
  monto: number | null;
  nota: string | null;
}

export interface NominaRef {
  hojaId: number;
  titulo: string;
  fecha: string | null;
}

export interface DetalleTrabajador {
  id: string;
  nombre: string;
  url: string;
  totalPrestamos: number | null;
  vales: Vale[];
  usados: number;
  capacidad: number;
  nominas: NominaRef[];
}

export interface DetalleNomina {
  trabajador: Trabajador;
  nomina: NominaRef;
  url: string;
  totalPrestamos: number | null;
  vales: Vale[];
}
