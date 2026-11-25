# Bot de Contabilidad

Bot multi-empresa para llevar la contabilidad diaria (gastos, pagos, retiros,
efectivo) en Google Sheets, operado por WhatsApp (Evolution API) con mensajes
de texto o de voz (Whisper + DeepSeek).

## Arquitectura

Cada módulo encapsula su propio servicio, interfaces (routers HTTP), DTOs y
herramientas:

```
src/
├── config/       # Settings inmutable desde .env, reloj (zona horaria) y logging
├── database/     # SQLite: conexión, modelos y BusinessRepository
├── auth/         # OAuth de Google con redirect, protegido con HTTP Basic
├── sheets/       # Cliente Google Sheets (batch, locks por planilla) + layout declarativo
├── drive/        # Cliente Google Drive (búsqueda directa por carpeta-mes)
├── accounting/   # Núcleo: comandos (patrón Command), dispatcher, sesiones, deshacer
├── ai/           # WhisperService (transcripción) y DeepSeekService (texto -> comandos JSON)
├── whatsapp/     # Webhook de Evolution API, DTOs y servicio de mensajería
├── main.py       # Composition root (inyección de dependencias)
└── cli.py        # Administración de businesses por línea de comandos
dev/              # Evolution API simulada y script para enviar mensajes (entorno local)
tests/            # Pruebas automáticas (pytest) con Google Sheets/Drive falsos
```

## Puesta en marcha

1. Copiar `.env.example` a `.env` y completar los valores. En particular:
   - `AUTH_ADMIN_PASSWORD`: contraseña larga y aleatoria para `/auth/*`
     (`python -c "import secrets; print(secrets.token_urlsafe(24))"`).
     **Sin ella `/auth/login` queda deshabilitado.**
   - `GOOGLE_ALLOWED_EMAILS`: cuenta(s) de Google con las que se permite
     autenticar el servidor.
   - `TIMEZONE` (por defecto `America/Bogota`).
2. En **Google Cloud Console**, registrar el redirect URI autorizado
   (valor de `GOOGLE_OAUTH_REDIRECT_URI`):
   `https://contabilidad.notiasis.com/auth/callback`
3. Registrar el primer business y su administrador:

```bash
uv run python src/cli.py add-business "Mi Negocio" <id_carpeta_drive_planillas> --workers-folder <id_carpeta_trabajadores>
uv run python src/cli.py add-admin 1 "Nombre Admin" 573001234567
```

4. Levantar el servidor:

```bash
uv run --directory src uvicorn main:app --host 0.0.0.0 --port 8000
```

5. **Autenticar con Google** (una sola vez, desde cualquier dispositivo):
   abrir `https://contabilidad.notiasis.com/auth/login`, ingresar el usuario y
   la contraseña de `AUTH_ADMIN_USER` / `AUTH_ADMIN_PASSWORD`, iniciar sesión
   con una cuenta de `GOOGLE_ALLOWED_EMAILS` y conceder permisos. El servidor
   guarda `token.json` automáticamente.

## Funcionalidades

### Varios comandos por mensaje

DeepSeek convierte cada mensaje en una lista JSON de comandos
(`{"comandos": ["gasto 5000 pan", "gasto 3000 leche"]}`) y el bot los ejecuta
en orden. "Gasto 5 mil de pan, 3 mil de leche y aseo 2 mil" registra tres
movimientos. Si el mensaje no trae ningún comando, el bot lo dice.

### Deshacer

`deshacer` revierte **todo lo que hizo el último mensaje** (todos sus
comandos), en orden inverso:

- Cada paso recuerda la fila exacta que escribió: un administrador nunca
  deshace lo que registró otro, aunque escriban en la misma planilla. Las
  filas de abajo suben una posición y el contador retrocede.
- `saldo` / `efectivo` restauran el valor anterior, salvo que alguien haya
  cambiado la celda después (en ese caso se avisa y no se pisa).
- La nómina también se deshace: se borra la hoja archivada y se restauran
  los vales y el contador del trabajador (si no se registraron vales nuevos
  después).
- "gasto 5000 pan y deshaz eso" deshace dentro del mismo mensaje.

### Planillas múltiples por día

Además de `hoja <dd-mm-aaaa>` (primera planilla del día), se pueden crear
planillas adicionales del mismo día:

```
segunda planilla     tercera planilla     2 planilla     3 planilla ...
```

- Se nombran `dd-mm-yyyy-2`, `dd-mm-yyyy-3`, etc., en la misma carpeta del mes.
- La planilla N toma como saldo de caja (B42) el saldo total (B58) de la
  planilla N-1 del mismo día.
- La primera planilla del día siguiente toma el saldo de la planilla MÁS
  ALTA del día anterior.
- El saldo se copia como número (se lee sin formato de moneda).
- Se deben crear en orden (no se puede crear la tercera sin la segunda).
- Por defecto usan la fecha de la planilla activa; también aceptan fecha
  explícita: `segunda planilla 24-08-2026`.

### Corregir saldos

`corregir_saldos` (o "corrige los saldos") recalcula el saldo efectivo (B42)
de **todas las planillas posteriores a la seleccionada**, en orden
cronológico (incluidas las adicionales del mismo día) hasta la última
creada: cada una toma el saldo total (B58) de la anterior, ya recalculado.
Se usa cuando se corrige una planilla vieja, porque el saldo se copia solo
al crear cada planilla.

- La planilla seleccionada no se modifica (es el punto de partida).
- Si faltan días entre dos planillas, el saldo pasa de la última existente
  a la siguiente.
- Sobrescribe B42 de las planillas siguientes (también si se había puesto a
  mano con `saldo`); la respuesta lista cada cambio y `deshacer` lo revierte.
- Si el saldo total de alguna planilla no es un número, se detiene ahí.

### Límites de las secciones

Cada sección de la planilla tiene un número fijo de filas (definido por las
fórmulas de la plantilla, ver `src/sheets/layout.py`). Cuando una sección se
llena, el bot rechaza el movimiento y sugiere crear una planilla adicional,
en vez de pisar la sección siguiente o los totales:

| Sección | Filas | Contador |
|---|---|---|
| Compras proveedores (A:B) | 11–34 | C135 |
| Préstamos trabajadores (C:D) | 11–26 | C136 |
| Administrador (E) | 26–34 | C137 |
| Retiros (C:E) | 39–59 | C138 |
| Inversiones (C:D) | 29–34 | C139 |
| Aseo (E) | 11–18 | C140 |
| Alimentación (E) | 20–24 | C141 |
| Vales del archivo de trabajador (principal!A:C) | 13–28 | principal!C123 |

### Préstamos a trabajadores

`trabajador <monto> <nombre>` registra un **préstamo** (no un pago de nómina):

1. Se registra en la planilla diaria (región de trabajadores). Si eso falla
   (ej: sección llena), no se toca el archivo del trabajador.
2. Además se registra en el **archivo individual del trabajador** (columna A:
   fecha, columna B: monto; fila según el contador en C123), dentro de la
   carpeta `workers_folder_id` del business:
   - La búsqueda ignora mayúsculas, tildes y ñ en ambos lados: "munoz perez"
     encuentra el archivo "Muñoz Pérez".
   - Si no existe archivo para ese nombre, se crea duplicando
     `WORKERS_TEMPLATE_ID` y se notifica con un mensaje aparte.
   - Si hay varios archivos con nombre similar, el bot envía un menú
     numerado y el usuario responde con el número de la opción (la última
     opción crea un trabajador nuevo). Si un mismo mensaje trae varios
     comandos ambiguos, se pregunta un menú a la vez.
   - **Si en vez del número llega cualquier otro mensaje**, el comando que
     preguntó se cancela completo: se borra de la planilla y el bot avisa
     que no se escogió ninguna opción. (Un número fuera de rango vuelve a
     mostrar el menú.)

`nomina <monto> <nombre>` (o `retiro <monto> nomina <nombre>`) cierra el
período: informa la suma de préstamos (B30), archiva la hoja principal con la
fecha de hoy (`dd-mm-aaaa`, o `dd-mm-aaaa (2)` si ya hubo otra nómina ese día)
y deja los vales en blanco.

Configurar la carpeta de trabajadores de un business:

```bash
uv run python src/cli.py set-workers-folder <business_id> <workers_folder_id>
```

### Zona horaria

El contenedor corre en UTC, pero todo lo que depende de "hoy" (la fecha que
DeepSeek usa para "la hoja de hoy", el nombre de la hoja de nómina, la fecha
por defecto de las planillas adicionales) usa `TIMEZONE`
(`America/Bogota` por defecto).

## Multi-empresa

- Cada business se identifica por el **número de WhatsApp** del remitente,
  registrado en `business_administrators`.
- Cada business tiene su propia carpeta de Drive (`sheets_folder_id` en la
  base de datos, ya no en `.env`).
- Al crear una planilla se escribe automáticamente: el nombre del business
  (A2:E2), el nombre del administrador (B6), la fecha (B7) y el saldo del
  día anterior (B42).
- Cada administrador tiene su propia sesión (planilla activa, deshacer y
  selección pendiente independientes). Las escrituras a una misma planilla
  se serializan con un lock por planilla, así dos administradores no se
  pisan filas.

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

| Método | Ruta | Protección | Descripción |
|---|---|---|---|
| GET | `/auth/login` | HTTP Basic | Redirige a Google para autenticar el servidor |
| GET | `/auth/callback` | `state` emitido por `/auth/login` (10 min) + cuenta permitida | Callback de Google (guarda `token.json`) |
| GET | `/auth/status` | HTTP Basic | Estado de las credenciales |
| POST | `/auth/refresh-token` | HTTP Basic | Refresca el token manualmente |
| POST | `/whatsapp/messages-upsert` | Red interna de Docker | Webhook de Evolution API (responde 200 de inmediato) |
| GET | `/whatsapp/messages/{id}/status` | Red interna de Docker | Estado del procesamiento de un mensaje (`processing` / `done` / `unknown`) |

El webhook responde a Evolution apenas llega el mensaje y lo procesa en
segundo plano (DeepSeek y Google pueden tardar), así Evolution no lo
reenvía. Los mensajes de un mismo remitente se procesan en orden de
llegada, y un mensaje con un id ya recibido se descarta.

## CLI

```bash
uv run python src/cli.py add-business <nombre> <sheets_folder_id> [--workers-folder <id>]
uv run python src/cli.py set-workers-folder <business_id> <workers_folder_id>
uv run python src/cli.py add-admin <business_id> <nombre> <telefono>
uv run python src/cli.py list-businesses
uv run python src/cli.py list-admins <business_id>
```

Dentro del contenedor Docker:

```bash
docker compose exec bot-contabilidad uv run python cli.py list-businesses
```

## Entorno local (servicios reales de DeepSeek y Google)

`docker-compose.local.yml` levanta el bot real (DeepSeek, Google Drive y
Sheets reales) junto con una **Evolution API simulada** (`dev/evolution_mock.py`)
que captura lo que el bot "envía por WhatsApp". Usa los archivos de la raíz
del proyecto: `.env`, `client_secret.json`, `token.json` y
`bot_contabilidad.db`.

```bash
docker compose -f docker-compose.local.yml up -d --build

# Enviar un mensaje como el administrador 999 y ver las respuestas del bot
uv run python dev/send.py "pon la hoja de hoy"
uv run python dev/send.py "gasto 5.000 pan y 3.000 leche"
uv run python dev/send.py --phone 998 "deshacer"
uv run python dev/send.py --audio nota.ogg      # requiere WHISPER_URL alcanzable

docker compose -f docker-compose.local.yml logs -f bot-contabilidad
docker compose -f docker-compose.local.yml down
```

El bot queda en `http://localhost:8000` (solo localhost) y la Evolution
simulada en `http://localhost:8081` (`GET /messages` lista lo enviado).

## Pruebas

```bash
uv run pytest
```

Las pruebas unitarias usan un Google Sheets/Drive falso en memoria que imita
la API (render sin formato/fórmulas, RAW vs USER_ENTERED, filas vacías
recortadas), con las plantillas reales resumidas.

Las pruebas **E2E** (de punta a punta, con DeepSeek y Google reales) corren
contra el entorno local y solo con `--e2e`:

```bash
docker compose -f docker-compose.local.yml up -d --build
uv run pytest --e2e -v
```

Ver [tests/e2e/README.md](tests/e2e/README.md).

### Cuota de Google Sheets

Google limita las escrituras a ~60 por minuto **por usuario**, y el bot usa
una sola cuenta para todos los negocios. El bot reintenta automáticamente
con espera (hasta ~2 minutos) cuando Google responde `429`. Si el volumen
crece, se puede pedir un aumento de la cuota "Write requests per minute per
user" en Google Cloud Console (APIs y servicios → Google Sheets API → Cuotas).

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
el compose solo las reenvía, sin valores hardcodeados. Variables nuevas que
también reenvía: `AUTH_ADMIN_USER`, `AUTH_ADMIN_PASSWORD`,
`GOOGLE_ALLOWED_EMAILS` y `TIMEZONE`.

> Nota: no existe servicio de base de datos en el compose porque SQLite es
> una base de datos embebida (un archivo), no un servidor: con el volumen
> persistente es suficiente.
