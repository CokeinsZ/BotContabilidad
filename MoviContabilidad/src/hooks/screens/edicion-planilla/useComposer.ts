import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import { Keyboard } from 'react-native';

import type { Comando } from '@/api';
import type { TextInputRef } from '@/components/ui/inputs';
import { completarNombre } from '@/utils/planillas/sugerenciasTrabajador';

import { LIBRE, composerInicial, composerReducer, envioDe } from './composer.reducer';

const PLACEHOLDER_LIBRE = 'Como en WhatsApp: gasto 5000 pan y 3000 leche';

/** Composer del chat: comando elegido, texto, foco y teclado. */
export function useComposer(comandos: Comando[], inicial: { comandoId: string; texto: string } | null) {
  const [state, dispatch] = useReducer(composerReducer, inicial ?? composerInicial);
  const inputRef = useRef<TextInputRef>(null);
  const abrirAlInicio = useRef(inicial !== null);

  const enfocar = useCallback(() => {
    setTimeout(() => inputRef.current?.focus(), 60);
  }, []);

  // Si se llegó con un comando (p. ej. "Registrar préstamo" desde un trabajador), el teclado se abre solo.
  useEffect(() => {
    if (abrirAlInicio.current) {
      abrirAlInicio.current = false;
      enfocar();
    }
  }, [enfocar]);

  const comando = useMemo(() => comandos.find((item) => item.id === state.comandoId) ?? null, [comandos, state.comandoId]);
  const esLibre = state.comandoId === LIBRE;

  const seleccionar = useCallback(
    (comandoId: string) => {
      const quitando = state.comandoId === comandoId;
      dispatch({ type: 'seleccionar', comandoId });
      if (quitando) Keyboard.dismiss();
      else enfocar();
    },
    [enfocar, state.comandoId],
  );

  return {
    comandoId: state.comandoId,
    comando,
    esLibre,
    activo: state.comandoId !== null,
    texto: state.texto,
    etiqueta: esLibre ? null : (comando?.etiqueta ?? null),
    placeholder: esLibre ? PLACEHOLDER_LIBRE : comando?.ejemplo ? `Ej: ${comando.ejemplo}` : 'Escribe el monto',
    puedeEnviar: envioDe(state) !== null,
    inputRef,
    seleccionar,
    cambiarTexto: (texto: string) => dispatch({ type: 'escribir', texto }),
    /** Borrar con el campo vacío quita el comando (como quitar una mención en WhatsApp). */
    borrarVacio: () => {
      if (state.texto === '') {
        dispatch({ type: 'deseleccionar' });
        Keyboard.dismiss();
      }
    },
    tomarEnvio: () => {
      const envio = envioDe(state);
      if (envio) dispatch({ type: 'enviado' });
      return envio;
    },
    completarTrabajador: (nombre: string) => {
      dispatch({ type: 'escribir', texto: `${completarNombre(state.texto, nombre)} ` });
      enfocar();
    },
  };
}
