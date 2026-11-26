export type TipoArgumentos = 'ninguno' | 'monto' | 'monto_texto' | 'monto_trabajador';

/** Un comando de la banda del chat (catálogo del bot). */
export interface Comando {
  /** Nombre del comando en el bot: "gasto", "trabajador"… */
  id: string;
  etiqueta: string;
  icono: string;
  argumentos: TipoArgumentos;
  ejemplo: string;
  ayuda: string;
  confirmar: boolean;
  sugiereTrabajador: boolean;
  alias: string[];
}
