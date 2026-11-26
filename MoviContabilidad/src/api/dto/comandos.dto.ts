export interface ComandoDto {
  id: string;
  etiqueta: string;
  icono: string;
  argumentos: 'ninguno' | 'monto' | 'monto_texto' | 'monto_trabajador';
  ejemplo: string;
  ayuda: string;
  confirmar: boolean;
  sugiere_trabajador: boolean;
  alias: string[];
}
