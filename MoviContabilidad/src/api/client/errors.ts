/**
 * Error de la API con el mensaje legible del servidor.
 *
 * El bot responde los errores de /app como `{ "detail": "...", "codigo": "..." }`.
 * Las pantallas muestran `message` y deciden por `codigo` (p. ej.
 * `GOOGLE_NO_CONECTADO`, `SIN_PREGUNTA`). `status` 0 = no hubo respuesta.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly codigo?: string;

  constructor(message: string, status: number, codigo?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.codigo = codigo;
  }
}

export const NETWORK_ERROR_MESSAGE = 'No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.';
export const TIMEOUT_MESSAGE = 'El servidor tardó demasiado en responder. Intenta de nuevo.';

export function isNetworkError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 0;
}

/** Errores que vale la pena reintentar solos: sin red o servidor caído (5xx). */
export function isRetryable(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 0 || error.status >= 500);
}

/** Mensaje para mostrarle al usuario a partir de cualquier error. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return 'Ocurrió un error inesperado.';
}
