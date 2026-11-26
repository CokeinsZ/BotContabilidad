import { ApiError } from './errors';
import { request } from './http';
import { onSessionExpired, onSessionRefreshed } from './sessionEvents';
import { getTokens, setTokens } from './tokens';

const PERFIL = {
  administrador: { id: 7, nombre: 'Marta', identificador: '999' },
  negocio: { id: 1, nombre: 'Panadería', carpeta_planillas_url: 'https://drive/x', carpeta_trabajadores_url: null },
  administradores: [],
  hoy: '24-11-2026',
  google_conectado: true,
  whatsapp_bot: null,
};

function json(status: number, body: unknown) {
  return Promise.resolve(new Response(body === undefined ? '' : JSON.stringify(body), { status }));
}

const fetchMock = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  (globalThis as { fetch: unknown }).fetch = fetchMock;
  setTokens(null);
});

test('adjunta el token de acceso', async () => {
  setTokens({ accessToken: 'acc-1', refreshToken: 'ref-1' });
  fetchMock.mockReturnValueOnce(json(200, { ok: true }));
  await expect(request('/perfil')).resolves.toEqual({ ok: true });
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toMatch(/\/app\/perfil$/);
  expect(init.headers.Authorization).toBe('Bearer acc-1');
});

test('varios 401 a la vez hacen UN solo refresh y reintentan con el token nuevo', async () => {
  setTokens({ accessToken: 'vencido', refreshToken: 'ref-1' });
  const refreshed = jest.fn();
  const stop = onSessionRefreshed(refreshed);
  fetchMock.mockImplementation((url: string, init: { headers: Record<string, string> }) => {
    if (url.endsWith('/auth/refresh')) {
      return json(200, { access_token: 'acc-2', expira_en: 3600, refresh_token: 'ref-2', perfil: PERFIL });
    }
    if (init.headers.Authorization === 'Bearer vencido') return json(401, { detail: 'vencido', codigo: 'TOKEN_INVALIDO' });
    return json(200, { ok: url });
  });

  await Promise.all([request('/perfil'), request('/comandos'), request('/trabajadores')]);
  const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).endsWith('/auth/refresh'));
  expect(refreshCalls).toHaveLength(1);
  expect(getTokens()).toEqual({ accessToken: 'acc-2', refreshToken: 'ref-2' });
  expect(refreshed).toHaveBeenCalledTimes(1);
  expect(refreshed.mock.calls[0][0].perfil.negocio.nombre).toBe('Panadería');
  stop();
});

test('si el refresh es rechazado, la sesión expira y se borran los tokens', async () => {
  setTokens({ accessToken: 'vencido', refreshToken: 'ref-viejo' });
  const expired = jest.fn();
  const stop = onSessionExpired(expired);
  fetchMock.mockImplementation((url: string) =>
    url.endsWith('/auth/refresh')
      ? json(401, { detail: 'Tu sesión terminó.', codigo: 'SESION_TERMINADA' })
      : json(401, { detail: 'vencido', codigo: 'TOKEN_INVALIDO' }),
  );
  await expect(request('/perfil')).rejects.toMatchObject({ status: 401 });
  expect(expired).toHaveBeenCalledTimes(1);
  expect(getTokens()).toEqual({ accessToken: null, refreshToken: null });
  stop();
});

test('sin red: error legible con status 0 y los tokens se conservan', async () => {
  setTokens({ accessToken: 'acc', refreshToken: 'ref' });
  fetchMock.mockRejectedValue(new TypeError('Network request failed'));
  const error = await request('/perfil').catch((e: unknown) => e);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 0, message: expect.stringContaining('No se pudo conectar') });
  expect(getTokens().refreshToken).toBe('ref');
});

test('los errores traen el detail y el codigo del bot', async () => {
  setTokens({ accessToken: 'acc', refreshToken: 'ref' });
  fetchMock.mockReturnValueOnce(json(503, { detail: 'El servidor no está conectado con Google.', codigo: 'GOOGLE_NO_CONECTADO' }));
  await expect(request('/planillas/meses')).rejects.toMatchObject({
    status: 503,
    codigo: 'GOOGLE_NO_CONECTADO',
    message: 'El servidor no está conectado con Google.',
  });
});

test('las rutas de /auth no llevan token', async () => {
  setTokens({ accessToken: 'acc', refreshToken: 'ref' });
  fetchMock.mockReturnValueOnce(json(201, { vinculacion_id: 'x' }));
  await request('/auth/vinculaciones', { method: 'POST', body: {}, auth: false });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
});
