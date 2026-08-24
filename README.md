# Bot de Contabilidad

Bot multi-empresa para llevar la contabilidad diaria (gastos, pagos, retiros,
efectivo) en Google Sheets, operado por WhatsApp (Evolution API) con mensajes
de texto o de voz (Whisper + DeepSeek).

## Arquitectura

Cada módulo encapsula su propio servicio, interfaces (routers HTTP), DTOs y
herramientas:

```
src/
├── config/       # Settings inmutable desde .env (singleton)
├── database/     # SQLite: conexión, modelos y BusinessRepository
├── auth/         # OAuth de Google con redirect (login remoto desde cualquier dispositivo)
├── sheets/       # Cliente Google Sheets (batchGet/batchUpdate) + layout declarativo
├── drive/        # Cliente Google Drive (búsqueda directa por carpeta-mes)
├── accounting/   # Núcleo: comandos (patrón Command), dispatcher, sesiones por usuario
├── ai/           # WhisperService (transcripción) y DeepSeekService (texto -> comando)
├── whatsapp/     # Webhook de Evolution API, DTOs y servicio de mensajería
├── main.py       # Composition root (inyección de dependencias)
└── cli.py        # Administración de businesses por línea de comandos
```

## Puesta en marcha

1. Copiar `.env.example` a `.env` y completar los valores.
2. En **Google Cloud Console**, registrar el redirect URI autorizado
   (valor de `GOOGLE_OAUTH_REDIRECT_URI`):
   `https://contabilidad.notiasis.com/auth/callback`
3. Registrar el primer business y su administrador:

```bash
python src/cli.py add-business "Mi Negocio" <id_carpeta_drive_planillas>
python src/cli.py add-admin 1 "Nombre Admin" 573001234567
```

4. Levantar el servidor:

```bash
uv run --directory src uvicorn main:app --host 0.0.0.0 --port 8000
```

5. **Autenticar con Google** (una sola vez, desde cualquier dispositivo):
   abrir `https://contabilidad.notiasis.com/auth/login`, iniciar sesión y
   conceder permisos. El servidor guarda `token.json` automáticamente.

## Multi-empresa

- Cada business se identifica por el **número de WhatsApp** del remitente,
  registrado en `business_administrators`.
- Cada business tiene su propia carpeta de Drive (`sheets_folder_id` en la
  base de datos, ya no en `.env`).
- Al crear una planilla se escribe automáticamente: el nombre del business
  (A2:E2), el nombre del administrador (B6), la fecha (B7) y el saldo del
  día anterior (B42).
- Cada administrador tiene su propia sesión (planilla activa y deshacer
  independientes).

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/auth/login` | Redirige a Google para autenticar el servidor |
| GET | `/auth/callback` | Callback de Google (guarda `token.json`) |
| GET | `/auth/status` | Estado de las credenciales |
| POST | `/auth/refresh-token` | Refresca el token manualmente |
| POST | `/whatsapp/messages-upsert` | Webhook de Evolution API |

## CLI

```bash
python src/cli.py add-business <nombre> <sheets_folder_id>
python src/cli.py add-admin <business_id> <nombre> <telefono>
python src/cli.py list-businesses
python src/cli.py list-admins <business_id>
```

## Despliegue con Docker

```bash
docker compose up -d --build
```

El compose monta un único volumen persistente: `/home/debian/secrets` del host
en `/app/secrets` del contenedor. Ahí deben colocarse los secretos y ahí se
generan los datos:

```
/home/debian/secrets/
├── client_secret.json        # se copia manualmente una vez
├── token.json                # lo genera el servidor tras /auth/login
└── data/
    └── bot_contabilidad.db   # lo crea la aplicación automáticamente
```

Las rutas dentro del contenedor (`/app/secrets/...`) se configuran en el
`.env` (`GOOGLE_CLIENT_SECRET_PATH`, `GOOGLE_TOKEN_PATH`, `DATABASE_PATH`);
el compose solo las reenvía, sin valores hardcodeados.

> Nota: no existe servicio de base de datos en el compose porque SQLite es
> una base de datos embebida (un archivo), no un servidor: con el volumen
> persistente es suficiente.
