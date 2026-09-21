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
uv run python src/cli.py add-business "Mi Negocio" <id_carpeta_drive_planillas>
uv run python src/cli.py add-admin 1 "Nombre Admin" 573001234567
```

4. Levantar el servidor:

```bash
uv run --directory src uvicorn main:app --host 0.0.0.0 --port 8000
```

5. **Autenticar con Google** (una sola vez, desde cualquier dispositivo):
   abrir `https://contabilidad.notiasis.com/auth/login`, iniciar sesión y
   conceder permisos. El servidor guarda `token.json` automáticamente.

## Funcionalidades

### Planillas múltiples por día

Además de `hoja <dd-mm-aaaa>` (primera planilla del día), se pueden crear
planillas adicionales del mismo día:

```
segunda planilla     tercera planilla     2 planilla     3 planilla ...
```

- Se nombran `dd-mm-yyyy-2`, `dd-mm-yyyy-3`, etc., en la misma carpeta del mes.
- La planilla N toma como saldo de caja (B42) el saldo total (B46) de la
  planilla N-1 del mismo día.
- La primera planilla del día siguiente toma el saldo de la planilla MÁS
  ALTA del día anterior.
- Se deben crear en orden (no se puede crear la tercera sin la segunda).
- Por defecto usan la fecha de la planilla activa; también aceptan fecha
  explícita: `segunda planilla 24-08-2026`.

### Préstamos a trabajadores

`trabajador <monto> <nombre>` registra un **préstamo** (no un pago de nómina):

1. Siempre se registra en la planilla diaria (región de trabajadores).
2. Además se registra en el **archivo individual del trabajador** (columna A:
   fecha, columna B: monto; fila según el contador en C123), dentro de la
   carpeta `workers_folder_id` del business:
   - Si no existe archivo para ese nombre, se crea duplicando
     `WORKERS_TEMPLATE_ID` y se notifica con un mensaje aparte.
   - Si hay varios archivos con nombre similar, el bot envía un menú
     numerado y el usuario responde con el número de la opción (la última
     opción crea un trabajador nuevo).

Configurar la carpeta de trabajadores de un business:

```bash
uv run python src/cli.py set-workers-folder <business_id> <workers_folder_id>
```

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

### Identificadores LID de WhatsApp

WhatsApp está migrando a identificadores privados (`@lid`); en ese caso el
número telefónico real **no llega en el webhook**. El bot resuelve así el
identificador del remitente (por prioridad):

1. `key.senderPn` (número real, cuando Evolution lo incluye).
2. La parte numérica del `remoteJid` (el número real si es `@s.whatsapp.net`,
   o el LID si es `@lid`).

Cuando alguien no registrado escribe al bot, este responde con su propio
identificador para poder darlo de alta directamente:

```
⚠️ Tu número no está registrado...
Tu identificador es: 4042000441346
```

Ese identificador (número real o LID) es el que se registra:

```bash
uv run python src/cli.py add-admin <business_id> "Stiven Carvajal" 4042000441346
```

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
uv run python src/cli.py add-business <nombre> <sheets_folder_id>
uv run python src/cli.py add-admin <business_id> <nombre> <telefono>
uv run python src/cli.py list-businesses
uv run python src/cli.py list-admins <business_id>
```

Dentro del contenedor Docker:

```bash
docker compose exec bot-contabilidad uv run python cli.py list-businesses
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
