/**
 * Transporte HTTP: el ÚNICO archivo de la app que usa `fetch` (lo vigila ESLint).
 *
 * Todo lo demás llama a funciones con nombre de negocio en `src/api/endpoints`.
 */
import { API_BASE_URL, DEFAULT_TIMEOUT_MS } from './config';
import { ApiError, NETWORK_ERROR_MESSAGE, TIMEOUT_MESSAGE } from './errors';

export type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export interface SendOptions {
  method?: HttpMethod;
  body?: unknown;
  query?: Record<string, string | number | null | undefined>;
  token?: string | null;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export function withQuery(path: string, query?: SendOptions['query']): string {
  if (!query) return path;
  const pairs = Object.entries(query)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
  return pairs.length ? `${path}?${pairs.join('&')}` : path;
}

/** Hace la petición. Lanza ApiError(status 0) si no hubo respuesta o se agotó el tiempo. */
export async function send(path: string, options: SendOptions = {}): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, options.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  const abortFromCaller = () => controller.abort();
  options.signal?.addEventListener('abort', abortFromCaller);

  try {
    return await fetch(`${API_BASE_URL}${withQuery(path, options.query)}`, {
      method: options.method ?? (options.body === undefined ? 'GET' : 'POST'),
      headers: {
        Accept: 'application/json',
        ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
    });
  } catch (cause) {
    if (options.signal?.aborted) throw cause;
    throw new ApiError(timedOut ? TIMEOUT_MESSAGE : NETWORK_ERROR_MESSAGE, 0);
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener('abort', abortFromCaller);
  }
}

/** JSON tipado de una respuesta. Lanza ApiError con el `detail` y `codigo` del servidor. */
export async function parse<T>(response: Response, path: string): Promise<T> {
  const text = await response.text().catch(() => '');
  let data: unknown;
  try {
    data = text.trim() === '' ? undefined : JSON.parse(text);
  } catch {
    if (response.ok) throw new ApiError(`Respuesta inválida del servidor en ${path}.`, response.status);
  }
  if (!response.ok) {
    const record = data !== null && typeof data === 'object' ? (data as Record<string, unknown>) : {};
    const detail = typeof record.detail === 'string' && record.detail.trim() !== ''
      ? record.detail
      : `Error ${response.status} del servidor.`;
    const codigo = typeof record.codigo === 'string' ? record.codigo : undefined;
    throw new ApiError(detail, response.status, codigo);
  }
  return data as T;
}
