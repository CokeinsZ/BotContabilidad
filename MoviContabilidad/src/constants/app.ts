/** Constantes de comportamiento de la app (no de diseño). */
export const APP = {
  /** Cada cuánto la pantalla de vinculación pregunta si el bot ya confirmó. */
  pairingPollMs: 2_000,
  /** Timeout normal de una petición. */
  requestTimeoutMs: 30_000,
  /** El chat espera más: DeepSeek + Google, con reintentos de cuota, pueden tardar ~2 min. */
  chatTimeoutMs: 150_000,
  /** El servidor recuerda una respuesta por client_id durante una hora (reintentos sin duplicar). */
  retryWindowMs: 60 * 60 * 1000,
  /** Mensajes del chat que se cargan por página. */
  chatPageSize: 50,
  /** Mensajes del chat más viejos que esto se borran del teléfono. */
  chatRetentionMs: 90 * 24 * 60 * 60 * 1000,
  /** Hojas que siempre se ofrecen en el selector (Primera, Segunda, Tercera). */
  minSheetOptions: 3,
  /** Retraso del toque simple cuando la fila también acepta doble toque. */
  doubleTapDelayMs: 260,
  /** Sugerencias de trabajadores que se muestran al escribir un préstamo o una nómina. */
  maxWorkerSuggestions: 5,
} as const;
