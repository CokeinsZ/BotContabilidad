/**
 * Estado del composer del chat (función pura, ver plan §12.2).
 *
 * - Elegir un comando abre el composer con su prefijo ("Gasto:").
 * - Elegir otro comando cambia el prefijo y conserva el texto.
 * - Elegir el mismo comando lo quita (y descarta el borrador).
 * - Al enviar, el comando SIGUE elegido para registrar varios seguidos.
 */
export const LIBRE = 'libre';

export interface ComposerState {
  /** null = sin comando (composer oculto). LIBRE = texto libre para DeepSeek. */
  comandoId: string | null;
  texto: string;
}

export type ComposerAction =
  | { type: 'seleccionar'; comandoId: string }
  | { type: 'deseleccionar' }
  | { type: 'escribir'; texto: string }
  | { type: 'enviado' };

export const composerInicial: ComposerState = { comandoId: null, texto: '' };

export function composerReducer(state: ComposerState, action: ComposerAction): ComposerState {
  switch (action.type) {
    case 'seleccionar':
      return state.comandoId === action.comandoId ? composerInicial : { comandoId: action.comandoId, texto: state.texto };
    case 'deseleccionar':
      return composerInicial;
    case 'escribir':
      return state.comandoId === null ? state : { ...state, texto: action.texto };
    case 'enviado':
      return { comandoId: state.comandoId, texto: '' };
    default:
      return state;
  }
}

/** Lo que se enviaría al bot, o null si todavía no hay nada que enviar. */
export function envioDe(state: ComposerState): { comando: string | null; texto: string } | null {
  if (state.comandoId === null) return null;
  const texto = state.texto.trim().replace(/\s+/g, ' ');
  if (!texto) return null;
  return { comando: state.comandoId === LIBRE ? null : state.comandoId, texto };
}
