export type AlertKind = 'info' | 'exito' | 'aviso' | 'error' | 'pregunta';

export interface AlertOptions {
  tipo?: AlertKind;
  titulo: string;
  mensaje?: string;
  /** Por defecto "Aceptar". */
  textoBoton?: string;
}

export interface ConfirmOptions {
  titulo: string;
  mensaje?: string;
  /** Por defecto "Confirmar". */
  textoConfirmar?: string;
  /** Por defecto "Cancelar". */
  textoCancelar?: string;
  /** Pinta el botón en rojo (acciones que no se pueden deshacer). */
  destructiva?: boolean;
}

export interface Alerts {
  /** Aviso con un solo botón. Se resuelve al cerrarlo. */
  mostrar: (options: AlertOptions) => Promise<void>;
  /** true si confirma; false si cancela, toca fuera o usa "atrás" en Android. */
  confirmar: (options: ConfirmOptions) => Promise<boolean>;
}
