# Plan: app móvil de Bot Contabilidad (MoviContabilidad)

> Escrito el 2026-11-24 sobre el commit `5f00088` ("Estructura base app movil") de la rama `general-fixes`.
> Las rutas y líneas citadas son de ese commit. Si el código cambió, verifíquenlas antes de editar.
>
> Este documento no depende de ninguna conversación. Dice qué se decidió, por qué, y cómo implementarlo en el
> backend (bot de Python, `src/`) y en la app (Expo, `MoviContabilidad/`).

## Estado (actualizado el 2026-11-26)

- **Decidido:** todo lo de este documento, incluidas las recomendaciones de §15, con tres cambios:
  - **El historial del chat se guarda solo en cada dispositivo** (SQLite en el teléfono, `localStorage` en la web),
    nunca en el servidor (ver §2.8 y §7.1).
  - **Entrega:** Android con un APK (EAS Build, perfil `preview`); **iPhone con la versión web** en Safari, pensada
    para el teléfono (no se paga el Apple Developer Program). La web de escritorio queda para después.
  - **El comando de préstamo se llama "Vale"** en la app; el bot acepta `vale`, `vales` y `v` como alias de
    `trabajador` (también por WhatsApp, vía el prompt de DeepSeek).
- **Backend:** todo §2, en el commit `b717c01` (PR #5). Después, en la rama `feature/app-movil`, una corrección:
  `src/google_api.py` usa **una conexión HTTP por hilo** para Google. Antes todas las peticiones compartían un solo
  `httplib2.Http`, que no es seguro entre hilos. Cuando la app pedía varias pantallas a la vez, OpenSSL mezclaba
  los datos (`SSLError: RECORD_LAYER_FAILURE`, falsos 404/502) y el bot moría con SIGSEGV. Con WhatsApp solo podía
  pasar con dos administradores escribiendo al mismo tiempo.
- **App:** implementada en `feature/app-movil`, sin commit: fases 0 a 6 de §14. Todas las pantallas de §10 y el chat
  completo de §12. Ícono a partir de `icono.jpg` (espiga de trigo), `app.json` y `eas.json` para Android, iOS y web.
  APK compilado en EAS el 2026-11-26 (perfil `preview`) y probado en el emulador contra el servidor real.
  Las diferencias con este plan están en la tabla siguiente.
- **Ojo con git:** la regla `data/` del `.gitignore` de la raíz (para la base local del bot) ignoraba también
  `MoviContabilidad/src/hooks/data/`. Los commits `0f7d5b3` y `a39df06` no tienen esos hooks, y el primer build de
  EAS falló por eso. Ahora la regla es `/data/` (solo la carpeta de la raíz): hay que agregar `src/hooks/data/` en
  el próximo commit.
- **Web:** `web.output: "single"` (SPA). `public/index.html` (viewport para el teléfono, manifiesto, íconos de
  "Agregar a inicio"), almacenamiento con `localStorage` (`*.web.ts`) y la raíz ajustada al visual viewport para el
  teclado (`VisualViewportRoot.web.tsx`). El bot acepta su dominio con `APP_WEB_ORIGINS` (CORS).
- **Verificado:**
  - Backend: `uv run pytest` → **148 pasan**. E2E con Google Drive/Sheets y DeepSeek reales
    (`uv run pytest --e2e`) → **47 pasan** (13 de la app, entre ellas lecturas concurrentes), 14 min.
  - Backend, 2026-11-26: `uv run pytest` → **155 pasan** (alias de vale, `APP_WEB_ORIGINS`). DeepSeek real
    convierte "vale 2000 prueba app" y "Vale de 3 mil para prueba app" en `trabajador …`.
  - App: `npx tsc --noEmit` y `npx expo lint` limpios; `npx jest` → 20 suites, **69 pruebas**; `expo-doctor` 20/20;
    `expo export` empaqueta para Android, iOS y web.
  - Web en Chrome del emulador de Android (build exportado, contra el bot local): vincular, Principal, Planillas,
    chat con el teclado abierto (encabezado visible, banda encima del teclado, Enter envía) y "Instalar app".
  - En el emulador de Android (Expo Go) contra el bot local: vincular (mensaje por el webhook simulado), Principal, crear y abrir
    planillas con el calendario, chat (gasto, reintento sin duplicar, "Libre" con DeepSeek, préstamo con sugerencia
    de trabajador, deshacer con confirmación), Resumen, Planillas (acordeón, toque simple, doble toque abre la app
    de Sheets), Trabajadores y detalle, Mi perfil y edición, Ayuda.
- **Falta:**
  - Publicar la web (p. ej. EAS Hosting) y poner su dominio en `APP_WEB_ORIGINS` del servidor.
  - Probar la web en Safari de un iPhone: el teclado (visual viewport) y "Agregar a pantalla de inicio".

### Diferencias entre este plan y lo implementado

| Plan | Implementado | Por qué |
|---|---|---|
| `react-native-keyboard-controller` + `KeyboardStickyFooter` | `KeyboardAvoider` (`ui/keyboard`): `KeyboardAvoidingView` de React Native con `behavior="padding"` y **sin** `keyboardVerticalOffset` | No viene en Expo Go. El encabezado de la app (`header` de JS) y el contenido son hermanos en un contenedor que empieza arriba de la ventana: sumar el alto del encabezado dejaba un hueco de ~110 dp sobre el teclado |
| `react-native-gesture-handler` en `TapArea` | `Pressable` + temporizador (`APP.doubleTapDelayMs` = 260 ms) | Toque, doble toque y mantener presionado sin dependencia nativa extra; probado en `TapArea.test.tsx` |
| `@react-native-async-storage/async-storage` | `expo-sqlite/kv-store` en el teléfono, `localStorage` en la web (`src/storage/kv/`) | `expo-sqlite` ya estaba; una dependencia menos |
| Web no era objetivo | Web para iPhone: `*.web.ts` en `src/storage/` (historial, clave-valor, token), `KeyboardAvoider.web.tsx`, `useKeyboardVisible.web.ts`, `VisualViewportRoot.web.tsx`, `public/index.html` | `expo-secure-store` no existe en la web, y `expo-sqlite` en la web exige cabeceras COOP/COEP (`credentialless`, que Safari no soporta). En Safari el teclado no achica la página: la raíz sigue al visual viewport |
| Refresh token **y perfil** en `expo-secure-store` | Solo el refresh token en el llavero; el perfil en caché, en `expo-sqlite/kv-store` | Algunas versiones de iOS rechazan valores de más de ~2 KB en el llavero, y el perfil crece con los administradores; si fallaba, fallaba la vinculación |
| `fetch` solo en `api/client/http.ts` | Solo en `api/client/transport.ts`; `http.ts` arma la petición, refresca y reintenta | Separar el transporte (timeout, abort, errores de red) de la lógica de sesión |
| `app/index.tsx` + `EntryRedirect` y `/principal` | Principal es `app/(app)/index.tsx` (`/`); `Stack.Protected` usa `redirectTo` | SDK 58 redirige solo cuando el guard es falso; no hace falta una ruta de entrada |
| `GestureHandlerRootView` y `KeyboardProvider` en `AppProviders` | `SafeAreaProvider` › `StatusBar` › `QueryProvider` › `AlertProvider` › `ToastProvider` › `SessionProvider` › `SplashGate` | Sin esas dos librerías. `SessionProvider` va dentro de `AlertProvider` porque avisa cuando la sesión vence |
| `authScreens.ts`, `useTecladoVisible`, `useSondeo`, `useValorDiferido`, `useRefrescarAlEnfocar` | `stackOptions.tsx`; `useKeyboardVisible` (en `ui/keyboard`); sondeo con `refetchInterval` de React Query; foco de la app con `focusManager` | Menos código propio donde React Query ya lo resuelve |
| `useActualizarNegocio` + `useActualizarAdministrador`; `useResponderSeleccion` + `useCancelarSeleccion` | `useActualizarPerfil` y `useSeleccion` (un hook por recurso) | Eran casi iguales |
| Editar negocio y Editar administrador con su propio formulario | Ambas pantallas pasan solo textos a `domain/perfil/FormularioNombre` (pantalla completa, "Guardar" inactivo si el nombre no cambió) | Eran casi idénticas |
| `GoldAccentBar`; `Row`, `Column` y `Spacer` en archivos separados | No existe `GoldAccentBar`; `Row`, `Column` y `Spacer` están juntos en `layout/Stacks.tsx` | No hizo falta; son tres envoltorios de pocas líneas |
| — | `src/storage/startup.ts` (abre la base, migra, marca `enviando` → `fallido`, limpia > 90 días) y `src/test-utils/TestProviders.tsx` | Arranque del almacenamiento antes de ocultar el splash; proveedores para pruebas |
| `jest.config.js` | Configuración de Jest en `package.json` con `moduleNameMapper` para el build CJS de `lucide-react-native` | La versión ESM no corre en Jest |

Detalles de Android encontrados en el emulador (ya corregidos):

- Una vista sin fondo ni borde se "aplana" en Fabric. Si después recibe fondo, pierde `borderRadius`: el día
  elegido del calendario salía cuadrado. Por eso `dayCircle` tiene fondo blanco desde el inicio.
- La `FlatList` `inverted` usa `scale: -1` en Android, que también voltea izquierda y derecha: el `paddingLeft` del
  contenedor aparecía a la derecha. El padding horizontal del chat va en cada fila.
- En el APK, Vincular quedaba bajo la barra de estado: el `paddingTop` de `contentStyle` reemplazaba el de la zona
  segura en `Screen`. Ahora se suma debajo de la zona segura (`Screen.test.tsx`).

## Índice

1. [Qué hace hoy el sistema (lo que la app debe respetar)](#1-qué-hace-hoy-el-sistema)
2. [Qué le falta al backend y cómo se resuelve](#2-backend-módulo-app)
3. [Arquitectura de la app](#3-arquitectura-de-la-app)
4. [Estructura de carpetas y archivos](#4-estructura-de-carpetas-y-archivos)
5. [Navegación (stack)](#5-navegación-stack)
6. [Autenticación en la app](#6-autenticación-en-la-app)
7. [Capa de datos](#7-capa-de-datos)
8. [Sistema de diseño: esquema y paleta](#8-sistema-de-diseño)
9. [Catálogo de componentes](#9-catálogo-de-componentes)
10. [Pantallas](#10-pantallas)
11. [Flujos](#11-flujos)
12. [Edición de planilla en detalle](#12-edición-de-planilla-en-detalle)
13. [Pruebas](#13-pruebas)
14. [Fases de implementación](#14-fases-de-implementación)
15. [Riesgos y decisiones abiertas](#15-riesgos-y-decisiones-abiertas)
16. [Pendiente de verificar en la documentación de Expo SDK 58](#16-pendiente-de-verificar-en-expo-sdk-58)

---

## 1. Qué hace hoy el sistema

### 1.1 Flujo de un mensaje

```
WhatsApp ──▶ Evolution API ──▶ POST /whatsapp/messages-upsert (responde 200 al instante)
                                   │  (en segundo plano, en orden por remitente)
                                   ▼
                    audio? ──▶ Whisper ──▶ texto
                                   ▼
                    DeepSeek: texto ──▶ {"comandos": ["gasto 5000 pan", ...]}
                                   ▼
            AccountingService.handle_commands(teléfono, comandos)
              ├─ BusinessRepository.find_context_by_phone → negocio + administrador
              ├─ SessionManager.get_or_create(negocio, teléfono) → sesión en memoria
              └─ CommandDispatcher.dispatch → Command.execute → Google Sheets / Drive
                                   ▼
                    respuestas (textos con emojis) ──▶ Evolution ──▶ WhatsApp
```

- Código: `src/whatsapp/whatsapp_service.py`, `src/accounting/accounting_service.py`, `src/accounting/dispatcher.py`.
- Un mensaje puede traer varios comandos; todos se agrupan en un solo "deshacer".

### 1.2 Identidad y multiempresa

- Cada administrador está en `business_administrators` con `phone_number`. **Ese valor puede ser el teléfono real o
  un LID de WhatsApp** (`@lid`), que no es un teléfono (ver README, "Identificadores LID").
- Los negocios y administradores se crean por CLI (`src/cli.py`). No hay contraseñas ni login de administradores.
- Tablas (`db.sql`): `businesses` (`name`, `sheets_folder_id`, `workers_folder_id`, `state`) y
  `business_administrators` (`business_id`, `name`, `phone_number`, `state`).

### 1.3 Planillas en Drive

```
<sheets_folder_id del negocio>/
├── octubre-2026/
├── noviembre-2026/            ← carpeta "mes-aaaa" (nombres en español, minúscula)
│   ├── 23-11-2026             ← primera planilla del día  (ordinal 1)
│   ├── 24-11-2026
│   ├── 24-11-2026-2           ← segunda planilla del día (ordinal 2)
│   └── 24-11-2026-3
```

- Se crean duplicando `PLANILLA_TEMPLATE_ID`. Al crear se escribe: A2 negocio, B6 administrador, B7 fecha y B42 =
  saldo total (B58) de la planilla anterior (la más alta del día anterior, o la N-1 del mismo día).
- Las adicionales se crean en orden: no hay tercera sin segunda (`src/accounting/commands/sheet_commands.py`).
- Celdas clave (`src/sheets/layout.py`): B38 gastos del día, B39 efectivo, B40 venta total, B42 saldo efectivo,
  B58 saldo total.

### 1.4 Comandos existentes

| Comando | Alias | Qué hace |
|---|---|---|
| `hoja <dd-mm-aaaa>` | planilla, h | Selecciona o crea la primera planilla del día |
| `segunda planilla [fecha]` | `2 planilla`, `2a planilla`, … hasta 31 | Planillas adicionales del día |
| `gasto <monto> <desc>` | g | Compras a proveedores (A11:B34) |
| `limpieza <monto>` | aseo, aseos, l | Aseo (E11:E18) |
| `alimentacion <monto>` | comida, a | Alimentación (E20:E24) |
| `trabajador <monto> <nombre>` | t, trabajadores | **Préstamo**: planilla (C11:D26) + archivo del trabajador |
| `nomina <monto> <nombre>` | n, nómina | Pago de nómina + cierre del período del trabajador |
| `administrador <monto>` | admin | Vale del administrador (E26:E34) |
| `retiro <monto> <desc>` | r | Retiro (C39:E59); si la descripción es `nomina <nombre>` también cierra el período |
| `inversion <monto> <desc>` | inv, inversiones | Inversiones (C29:D34) |
| `saldo <monto>` | s | Sobrescribe B42 |
| `efectivo <monto>` | e | Sobrescribe B39 |
| `terminar_dia` | resumen | Totales + link |
| `corregir_saldos` | corregir saldos, recalcular_saldos | Re-encadena B42 de todas las planillas posteriores |
| `deshacer` | undo | Revierte todo lo del último mensaje |
| `instrucciones` | i, help, ayuda | Ayuda |

Comportamientos que la app tiene que respetar:

- **Sesión en memoria por (negocio, teléfono)**: planilla activa, último deshacer y cola de menús pendientes
  (`src/accounting/session_manager.py`).
- **Menús numerados**: si hay varios trabajadores con nombre parecido, el bot pregunta y espera un número. Cualquier
  otro mensaje cancela el comando completo y lo borra de la planilla.
- **Límites por sección**: si una sección se llena, el bot rechaza y sugiere "segunda planilla".
- **Trabajadores**: un archivo por trabajador en `workers_folder_id`; hoja `principal`, vales en A13:C28 (A fecha,
  B monto), contador C123, total B30. La nómina archiva la hoja como `dd-mm-aaaa` (o `dd-mm-aaaa (2)`), **borra las
  filas 1–9 de la copia** y limpia los vales.
- **Cuota de Google**: ~60 escrituras y ~60 lecturas por minuto por usuario, y el bot usa una sola cuenta para todos
  los negocios. Cada lectura que haga la app cuesta cuota: hay que leer poco y de forma perezosa.
- **Respuestas**: textos en español con emojis al inicio (`✅`, `⚠️`, `📄`, `👤`, `📋`, `🔄`, `⏳`, `🤔`).

### 1.5 Endpoints actuales

Solo `/auth/*` (OAuth de Google del servidor, protegido con HTTP Basic) y `/whatsapp/*` (webhook interno).
**No existe una API para clientes ni autenticación de administradores.** Eso es lo primero que hay que construir.

---

## 2. Backend: módulo `app`

### 2.1 Autenticación: vinculación por WhatsApp

**Decisión:** el administrador entra a la app **vinculándola desde su WhatsApp**, no con usuario y contraseña ni con un
código enviado a su teléfono.

**Por qué:**

- `phone_number` puede ser un LID. No sabemos el teléfono real de esos administradores, así que no podemos pedirles
  "escribe tu número" ni enviarles un código a un número.
- El bot ya sabe identificar a quien le escribe (teléfono o LID). Si el administrador le manda un código al bot, el bot
  sabe exactamente quién es, igual que con cualquier comando.
- No hay contraseñas que guardar, olvidar ni recuperar. El registro sigue siendo por CLI.

**Flujo:**

```
App                                   Backend                               WhatsApp
 │ POST /app/auth/vinculaciones ─────▶ crea {id secreto, código 6 dígitos,
 │                                       expira en 5 min}
 │◀── {vinculacion_id, codigo, whatsapp_url, expira_en}
 │
 │ abre whatsapp_url  (wa.me/<BOT>?text=VINCULAR%20482913) ──────────────▶ el usuario toca "Enviar"
 │                                      ◀── webhook "VINCULAR 482913" (antes de DeepSeek)
 │                                      identifica al admin por teléfono/LID
 │                                      marca la vinculación como confirmada
 │                                      ──▶ "✅ App vinculada. Si no fuiste tú, escribe 'cerrar app'."
 │ GET /app/auth/vinculaciones/{id}  (cada 2 s, máx. 5 min)
 │◀── {estado: "confirmada", access_token, refresh_token, perfil}   ← se entrega UNA sola vez
```

Reglas:

- El código es de 6 dígitos, dura 5 minutos y sirve una sola vez. El `vinculacion_id` es un UUID aleatorio
  (128 bits) que solo conoce la app: aunque alguien vea el código, sin el id no recibe los tokens.
- Los tokens se entregan una vez (estado `confirmada` → `consumida`). Una segunda consulta devuelve `consumida` sin
  tokens.
- Si quien envía el código no está registrado, el bot responde lo mismo que hoy (su identificador para darlo de alta).
- Límite simple en memoria: máximo 10 vinculaciones por IP cada 10 minutos.
- `cerrar app` desde WhatsApp revoca todas las sesiones de la app de ese administrador (útil si pierde el teléfono).

**Tokens:**

| Token | Formato | Vida | Dónde vive |
|---|---|---|---|
| Acceso | JWT HS256: `sub`=admin_id, `bid`=business_id, `exp` | 60 min | Memoria de la app |
| Refresco | 32 bytes aleatorios (base64url), guardado como SHA-256 en `app_sessions` | 90 días, **rotación en cada uso** | `expo-secure-store` |

En cada petición la dependencia `current_admin` valida el JWT **y** revisa en SQLite que el administrador y el
negocio sigan `active` (consulta barata; así desactivar a alguien por CLI lo saca de la app de inmediato).

### 2.2 Sesión del bot separada por canal

**Problema:** la sesión del bot es única por (negocio, teléfono). Si la app y WhatsApp la comparten, un `deshacer`
en WhatsApp revertiría lo que se hizo en la app, y la planilla activa saltaría de un lado a otro.

**Decisión:** la clave de la sesión pasa a ser `(business_id, phone_number, channel)` con `channel ∈ {"whatsapp", "app"}`.
WhatsApp y la app tienen planilla activa, deshacer y menús independientes. Las escrituras a una misma planilla ya se
serializan con el lock por planilla de `SheetsClient`, así que no se pisan filas.

### 2.3 Endpoints nuevos (`/app`)

Todos devuelven JSON con claves en español `snake_case`. Todos, salvo `/app/auth/*`, exigen
`Authorization: Bearer <access_token>`. Errores: `{ "detail": "<mensaje legible>", "codigo": "<CODIGO>" }`.

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/app/auth/vinculaciones` | Crea una vinculación (`{dispositivo}` opcional) |
| GET | `/app/auth/vinculaciones/{id}` | Estado: `pendiente` / `confirmada` (+tokens, una vez) / `consumida` / `expirada` |
| POST | `/app/auth/refresh` | `{refresh_token}` → nuevo par (rota el refresh) |
| POST | `/app/auth/logout` | Revoca el refresh actual |
| GET | `/app/perfil` | Administrador, negocio, otros administradores, `hoy` (zona del negocio), `google_conectado`, `whatsapp_bot` |
| PATCH | `/app/negocio` | `{nombre}` |
| PATCH | `/app/administrador` | `{nombre}` |
| GET | `/app/comandos` | Catálogo de comandos para la banda del chat |
| GET | `/app/planillas/meses` | Carpetas `mes-aaaa` del negocio, de la más reciente a la más antigua |
| GET | `/app/planillas?anio=2026&mes=11` | Planillas de un mes (`[]` si la carpeta no existe) |
| GET | `/app/planillas/hoy` | Planillas de hoy + totales de la última (tarjeta de la pantalla Principal) |
| POST | `/app/planillas` | `{fecha, hoja}` → crea o abre (reutiliza los comandos `hoja` / `N planilla`) |
| GET | `/app/planillas/{id}` | Metadatos: nombre, fecha, hoja, url |
| GET | `/app/planillas/{id}/resumen` | Totales (B38–B58) + uso de cada sección (contadores C135:C141) |
| GET | `/app/planillas/{id}/estado` | Menú pendiente y qué revertiría `deshacer` (al abrir el chat). El historial NO viene del servidor |
| POST | `/app/planillas/{id}/mensajes` | `{client_id, comando?, texto}` → respuestas del bot (no se guardan en el servidor) |
| POST | `/app/planillas/{id}/seleccion` | `{opcion}` → responde el menú pendiente |
| DELETE | `/app/planillas/{id}/seleccion` | Cancela el menú pendiente (revierte el comando que preguntó) |
| GET | `/app/trabajadores` | Lista (solo nombres: leer el total de cada uno costaría una lectura por trabajador) |
| GET | `/app/trabajadores/{id}` | Período actual (vales, total B30, usados/16) + nóminas archivadas |
| GET | `/app/trabajadores/{id}/nominas/{hoja_id}` | Vales y total de una nómina archivada |

### 2.4 Contratos clave

`POST /app/planillas` (crear o abrir):

```json
// petición
{ "fecha": "24-11-2026", "hoja": 2 }
// 201 creada / 200 ya existía
{
  "planilla": { "id": "1AbC…", "nombre": "24-11-2026-2", "fecha": "24-11-2026", "hoja": 2,
                "url": "https://docs.google.com/spreadsheets/d/1AbC…/edit" },
  "creada": true,
  "avisos": ["Saldo de caja cargado desde '24-11-2026'."]
}
// 422 si el bot no pudo (p. ej. "No existe la planilla '24-11-2026'. Las planillas adicionales se crean en orden.")
```

`POST /app/planillas/{id}/mensajes`:

```json
// petición
{ "client_id": "0b6f2c9e-uuid", "comando": "gasto", "texto": "5.000 pan" }
// respuesta (la app guarda el mensaje enviado y estas respuestas en su SQLite)
{
  "client_id": "0b6f2c9e-uuid",
  "comandos": ["gasto 5000 pan"],
  "interpretado_por_ia": false,
  "respuestas": [{ "tipo": "exito", "texto": "Gasto registrado: $5.000 - pan" }],
  "estado": { "seleccion": null, "deshacer": "gasto 5000 pan" },
  "procesado_en": "2026-11-24T15:02:13-05:00"
}
```

Menú pendiente (cuando hay varios trabajadores parecidos). La respuesta que era el menú numerado llega con
`"tipo": "seleccion"` y el texto de la pregunta:

```json
"seleccion": {
  "pregunta": "Hay varios trabajadores con nombre similar a 'jose'",
  "opciones": [
    { "valor": 1, "etiqueta": "jose salon", "crea": false },
    { "valor": 2, "etiqueta": "jose panadero", "crea": false },
    { "valor": 3, "etiqueta": "Crear nuevo trabajador 'jose'", "crea": true }
  ],
  "comando": "trabajador 20000 jose",
  "planilla_id": "1AbC…",
  "planilla_nombre": "24-11-2026"
}
```

`tipo` de cada mensaje del bot: `exito` | `aviso` | `error` | `info` | `seleccion`. Se calcula en el backend
(`message_kinds.py`) a partir del emoji inicial y se quita el emoji del texto (la app pone su propio ícono).

`GET /app/comandos`:

```json
[
  { "id": "gasto", "etiqueta": "Gasto", "icono": "gasto", "argumentos": "monto_texto",
    "ejemplo": "5.000 pan", "ayuda": "Compras a proveedores", "confirmar": false, "sugiere_trabajador": false },
  { "id": "trabajador", "etiqueta": "Préstamo", "icono": "prestamo", "argumentos": "monto_trabajador",
    "ejemplo": "20.000 juan", "ayuda": "Préstamo a un trabajador", "confirmar": false, "sugiere_trabajador": true },
  { "id": "deshacer", "etiqueta": "Deshacer", "icono": "deshacer", "argumentos": "ninguno",
    "ejemplo": "", "ayuda": "Revierte tu último mensaje", "confirmar": true, "sugiere_trabajador": false }
]
```

`argumentos`: `ninguno` | `monto` | `monto_texto` | `monto_trabajador`. Orden recomendado de la banda (por frecuencia):
Gasto, Efectivo, Saldo, Préstamo, Retiro, Aseo, Alimentación, Vale admin, Inversión, Nómina, Resumen, Deshacer,
Corregir saldos. `hoja` / `N planilla` **no** van en la banda (las planillas se eligen en sus pantallas) e
`instrucciones` abre la pantalla Ayuda.

### 2.5 Cómo procesa el backend un mensaje de la app

`chat_service.send(admin, sheet_id, client_id, comando, texto)`:

1. **Pertenencia**: verifica que `sheet_id` sea de este negocio (padre = carpeta `mes-aaaa` cuyo padre es
   `sheets_folder_id`). Se cachea en memoria `sheet_id → (business_id, nombre)`. Si no, 404.
2. **Idempotencia**: si `client_id` ya se procesó, devuelve el mismo resultado. Así un reintento por mala señal no
   registra dos veces el mismo gasto (equivale al descarte de ids repetidos de Evolution). Las respuestas se
   recuerdan **en memoria durante una hora** (no en disco). Un reintento después de una hora o de reiniciar el
   servidor sí se registraría de nuevo: la app solo ofrece "Reintentar" dentro de esa hora.
3. **Construir comandos** (`command_builder.py`):
   - Comando sin argumentos (`deshacer`, `terminar_dia`, `corregir_saldos`) → `[comando]`.
   - Comando con argumentos y texto que pasa el **parser estricto** → directo, **sin DeepSeek** (más rápido,
     determinista y sin costo). El parser acepta el monto al inicio o al final: `"5.000 pan"` o `"pan 5.000"` →
     `gasto 5000 pan`; `"juan 20000"` → `trabajador 20000 juan`. Usa `parse_amount` de `accounting/money.py`.
   - Si no pasa (`"5 mil de pan"`, `"dos lucas"`) → DeepSeek con `"<comando> <texto>"`.
   - Sin comando (chip "Libre") → DeepSeek con el texto tal cual (permite "gasto 5000 pan y 3000 leche").
   - Si DeepSeek devuelve `hoja` o `N planilla`, se descartan y se responde "Para cambiar de planilla usa la
     pantalla Planillas".
4. `AccountingService.select_sheet(..., channel="app")` fija la planilla activa del canal app.
5. `AccountingService.handle_commands(phone, comandos, channel="app")` en un hilo (`asyncio.to_thread`), con un lock
   por (administrador, canal) para procesar en orden, igual que WhatsApp.
6. Clasifica las respuestas y arma `estado` (menú pendiente y descripción del deshacer). **No las guarda**: el
   historial vive en el teléfono.

Crear o abrir una planilla (`POST /app/planillas`) usa `AccountingService.run_detached`: corre el comando en una
sesión temporal, así no cancela una pregunta pendiente del chat ni reemplaza el deshacer. Un lock por
(negocio, nombre de planilla) evita que dos toques seguidos dupliquen el archivo en Drive.

### 2.6 Cambios en archivos existentes (implementados)

| Archivo | Cambio |
|---|---|
| `db.sql` | Tablas `app_pairings` y `app_sessions` (ver 2.8). Son nuevas: `CREATE TABLE IF NOT EXISTS` basta, no hace falta migración |
| `src/config/settings.py` | `APP_JWT_SECRET`, `APP_ACCESS_TOKEN_MINUTES` (60), `APP_REFRESH_TOKEN_DAYS` (90), `BOT_WHATSAPP_NUMBER` |
| `.env.example`, `docker-compose.yml` | Las mismas variables |
| `pyproject.toml`, `uv.lock` | `pyjwt` 2.15.1 |
| `src/accounting/session_manager.py` | Clave `(business_id, phone, channel)` con `WHATSAPP` / `APP`. `PendingSelection` guarda `prompt`, `option_labels` y la planilla donde se preguntó. `SessionState` (foto de solo lectura de la sesión) |
| `src/accounting/commands/employee_commands.py` | `menu_prompt` y `menu_labels`; `ask_selection` guarda la pregunta y las etiquetas. El texto del menú de WhatsApp no cambió |
| `src/accounting/accounting_service.py` | `channel` en `handle_commands` y `has_pending_selection` (por defecto WhatsApp). Nuevos: `google_connected`, `select_sheet`, `session_state`, `cancel_pending`, `run_detached` y la función `unregistered_message` |
| `src/accounting/dispatcher.py` | `resolve(texto)` (qué comando ejecutaría, sin ejecutarlo) y `commands` |
| `src/drive/drive_client.py` | `try_list_files_in_folder`, `list_month_folders`, `list_planillas_of_month`, `get_file` (nombre, padres, tipo) |
| `src/sheets/layout.py` | `DAILY_REGION_ATTRS`, `daily_regions`, `worker_archive_offset` (= 9), `SheetRegion.moved()` y `sheet_prefix()` para leer hojas archivadas |
| `src/sheets/sheets_client.py` | `get_planilla_overview`: totales + contadores de las 7 secciones en **un** `batchGet` (`get_daily_totals` lo reutiliza) |
| `src/database/business_repository.py` | `find_context_by_admin_id`, `update_business_name`, `update_administrator_name` |
| `src/whatsapp/whatsapp_service.py` | Antes de DeepSeek: `VINCULAR <6 dígitos>` y `cerrar app` se responden directo y no tocan la contabilidad (no cancelan un menú pendiente). Dependencia opcional `app_auth` |
| `src/main.py` | Construye `AppRepository`, `AppAuthService` y la API de la app; avisa al arrancar si faltan `APP_JWT_SECRET` o `BOT_WHATSAPP_NUMBER`; CORS acepta PATCH y DELETE |
| `tests/fakes.py`, `tests/conftest.py` | `FakeDrive` con carpetas de mes, padres y archivos de otro negocio; `FakeSheetsClient` se movió a `fakes.py` |
| `README.md` | Sección "App móvil" y endpoints `/app` |

### 2.7 Archivos nuevos del backend (implementados)

Mismo patrón que los módulos actuales (servicios + controladores + DTOs, inyección en `main.py`):

```
src/
├── database/
│   └── app_repository.py          # vinculaciones y sesiones (nada de mensajes)
└── mobile/
    ├── __init__.py                # exporta create_mobile_api, install_mobile_api, AppAuthService, TokenService
    ├── api.py                     # arma servicios (create_mobile_api) y los publica bajo /app con el formato de errores
    ├── errors.py                  # AppError y subclases → {"detail", "codigo"}
    ├── dto.py                     # contrato JSON (pydantic) y conversores dataclass → JSON
    ├── cache.py                   # TtlCache: listados de Drive (30 s) y respuestas ya entregadas (1 h)
    ├── locks.py                   # KeyedLocks: por administrador y por planilla en creación
    ├── google_gate.py             # 503 GOOGLE_NO_CONECTADO si el servidor no tiene credenciales
    ├── values.py                  # números de celda → JSON, URLs de Sheets y Drive
    ├── catalog.py                 # catálogo de comandos de la banda
    ├── ownership.py               # verifica que planillas/trabajadores sean del negocio (con caché)
    ├── planillas_service.py       # meses, mes, hoy, crear/abrir, detalle, resumen
    ├── workers_service.py         # lista, período actual, nómina archivada
    ├── profile_service.py         # perfil y cambio de nombres
    ├── security/
    │   ├── tokens.py              # JWT de acceso (PyJWT) y refresh opaco
    │   ├── rate_limit.py          # límite por IP para pedir códigos
    │   └── dependencies.py        # API habilitada + current_context (Bearer)
    ├── auth/
    │   └── auth_service.py        # vincular, confirmar desde WhatsApp, entregar, refrescar, cerrar, autenticar
    ├── chat/
    │   ├── command_builder.py     # lectura directa + respaldo DeepSeek + filtro de comandos de planilla
    │   ├── message_kinds.py       # emoji inicial → tipo; limpia el texto
    │   └── chat_service.py        # enviar, responder/cancelar pregunta, estado
    └── controllers/
        ├── auth_controller.py
        ├── profile_controller.py
        ├── commands_controller.py
        ├── planillas_controller.py
        ├── chat_controller.py
        └── workers_controller.py
dev/
└── app_login.py                   # vincula la "app" contra el bot local y muestra los tokens
tests/
├── test_mobile_units.py           # parser, tipos de respuesta, tokens, catálogo, límites, caché
└── test_mobile_api.py             # la API de punta a punta con SQLite real y Google falso
```

Notas de implementación:

- **Catálogo**: `catalog.py` mapea nombre de comando → metadatos de interfaz. `test_every_catalog_command_exists_in_the_dispatcher`
  falla si alguien renombra un comando.
- **Trabajadores**: los vales se leen de `principal!A13:C28` (UNFORMATTED); una fila es vale si A no está vacía o B ≠ 0
  (la plantilla trae 0 en B). Usados = C123 − 13. En una nómina archivada se borraron las filas 1–9, así que los vales
  están en `A4:C19` y el total en `B21`; se calcula con `worker_archive_offset` y `SheetRegion.moved()`.
- **Pertenencia de trabajadores**: el padre del archivo debe ser `workers_folder_id` (una llamada, cacheada).
- **Caché de 30 s** para meses, mes, hoy, totales y trabajadores. Se invalida al crear una planilla y después de
  cada mensaje del chat (totales y tarjeta de hoy; trabajadores si el comando fue préstamo, nómina o retiro).
- **Tiempo de respuesta**: el endpoint de mensajes espera el resultado (a diferencia del webhook). Con reintentos de
  cuota puede tardar hasta ~2 min; la app usa un timeout de 150 s para ese endpoint.

### 2.8 Tablas nuevas (servidor)

Solo lo necesario para autenticar. Los tiempos son segundos Unix en INTEGER (se comparan en Python sin depender
del formato de fecha de SQLite).

```sql
CREATE TABLE IF NOT EXISTS app_pairings (
    id TEXT PRIMARY KEY,                       -- secreto aleatorio que solo conoce la app
    code TEXT NOT NULL,                        -- 6 dígitos que viajan por WhatsApp
    device_name TEXT,
    administrator_id INTEGER,                  -- se llena al confirmar desde WhatsApp
    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'confirmed', 'consumed')),
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (administrator_id) REFERENCES business_administrators(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS app_sessions (
    id INTEGER PRIMARY KEY,
    administrator_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL UNIQUE,   -- SHA-256, nunca el token en claro
    device_name TEXT,
    created_at INTEGER NOT NULL,
    last_used_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked_at INTEGER,
    FOREIGN KEY (administrator_id) REFERENCES business_administrators(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**El historial del chat no está en el servidor.** Cada teléfono lo guarda en su propio SQLite (§7.1). Consecuencias:

- Dos administradores que usan la misma planilla no ven en el chat lo que escribió el otro. Lo ven en los totales,
  en el Resumen y en Google Sheets.
- Si se reinstala la app o se cambia de teléfono, el historial del chat se pierde. Lo registrado en las planillas
  no se pierde.

### 2.9 Despliegue

- Exponer `/app/*` por HTTPS en el mismo dominio (`contabilidad.notiasis.com`) desde el proxy. `/whatsapp/*` sigue
  siendo solo de la red interna.
- CORS no aplica a apps nativas; no hace falta tocarlo.

---

## 3. Arquitectura de la app

### 3.1 Stack

La base existente (`MoviContabilidad/package.json`) es Expo SDK 58, React Native 0.88, React 19.3, expo-router 58 con
`typedRoutes`. Se agrega, siempre con `npx expo install <paquete>`:

| Paquete | Para qué |
|---|---|
| `expo-secure-store` | Guardar el refresh token |
| `expo-sqlite` | **Historial del chat en el teléfono** (nunca en el servidor) |
| `@tanstack/react-query` | Caché, recarga al volver a la pantalla, estados de carga/error. Evita repetir en cada pantalla el patrón `useFocusEffect + AbortController + useState` que ZoneUp escribe a mano |
| `react-hook-form` | Formularios (como ZoneUp) |
| ~~`react-native-gesture-handler`~~ | No se usó: `TapArea` distingue toque y doble toque con un temporizador |
| ~~`react-native-keyboard-controller`~~ | No se usó (no viene en Expo Go): `KeyboardAvoidingView` de React Native |
| `react-native-reanimated` (ya está) | Acordeones, aparición del composer, chips |
| `lucide-react-native` + `react-native-svg` | Íconos de trazo uniforme |
| `expo-font` + `@expo-google-fonts/inter` + `@expo-google-fonts/playfair-display` | Tipografía |
| `expo-intent-launcher` | Abrir la planilla directamente en la app Google Sheets en Android |
| `expo-clipboard` | Copiar mensaje / enlace |
| `expo-haptics` | Vibración corta al enviar y al elegir un comando |
| `expo-device` | Nombre del dispositivo para la vinculación ("iPhone de Stiven") |
| `expo-sqlite/kv-store` (en lugar de async-storage) | Preferencias pequeñas (p. ej. "ya vi la pista del doble toque") |
| dev: `jest-expo`, `@testing-library/react-native` | Pruebas |

Se quitan de la plantilla: `expo-symbols` (se usa lucide), `expo-web-browser` (no se necesita), y `react-dom` /
`react-native-web` si se confirma que la web no es objetivo. `app.json`: `"userInterfaceStyle": "light"`,
`"platforms": ["ios", "android"]`.

### 3.2 Qué tomamos de ZoneUp y qué mejoramos

| ZoneUp hace | Aquí |
|---|---|
| `SessionProvider` + `useSession()` + `Stack.Protected` en el layout raíz + grupo `(auth)` | **Igual**, más: sesión persistente (ZoneUp pierde el token al cerrar la app), restauración al abrir, refresco automático ante 401 y estado `restaurando` que mantiene el splash |
| `src/api/client.ts` es el único `fetch`; un archivo por recurso; `toUser()` convierte respuestas | **Igual**, separado en carpetas: `client/`, `endpoints/`, `dto/`, `entities/`, `mappers/`. Y una regla de ESLint que prohíbe `fetch` fuera de `src/api/client/transport.ts` |
| Archivos de `app/` que solo llaman a un componente | **Más limpio**: re-exportan el componente en una línea (`export { default } from …`) |
| Layouts con la lista de `Stack.Screen` y títulos | Los títulos y opciones viven en `src/navigation/`; el layout solo los recorre |
| Hooks por pantalla en `src/hooks/<área>/` | **Igual** (`hooks/screens/`), más hooks de datos compartidos (`hooks/data/`) |
| Componentes en la raíz de `components/` (`Button`, `Field`, `Select`, `SelectFiltro`, `CampoBusqueda`, `GlassCard`, `DashboardNavTile`, `DashboardStat`…) con lógica repetida (cada uno filtra `className` y decide "liquid o respaldo" por su cuenta) | **Familias en carpetas** (`ui/buttons`, `ui/inputs`, `ui/backgrounds`…), **una variante es una prop, no un componente nuevo**, y la lógica compartida (estilos por tono, tamaños) sale de `theme/` una sola vez |
| Tailwind (uniwind) con clases que cada componente tiene que limpiar | `StyleSheet` + tokens tipados de `src/theme`. Sin clases que filtrar y con autocompletado de colores |

### 3.3 Capas y reglas de dependencia

```
app/  (solo enrutamiento)
  └─▶ components/screens/<pantalla>        (arma la pantalla, sin lógica)
        ├─▶ hooks/screens/<pantalla>       (estado y acciones de la pantalla)
        │     ├─▶ hooks/data/<recurso>     (React Query)
        │     │     └─▶ api/endpoints      (únicos que llaman a http.ts)
        │     ├─▶ session/
        │     ├─▶ navigation/routes
        │     └─▶ utils/
        └─▶ components/{ui, domain, navigation}
              └─▶ theme/, utils/   (ui/ nunca importa api/, session/ ni hooks/data/)
```

Reglas (se hacen cumplir con `no-restricted-imports` / `no-restricted-globals` en ESLint):

1. `fetch` solo existe en `src/api/client/transport.ts` (lo usa `http.ts`).
2. `components/ui/` no importa de `api/`, `session/`, `hooks/` ni `domain/`. Es reutilizable en cualquier proyecto.
3. `components/domain/` solo importa **tipos** de `api/entities`.
4. `app/` solo re-exporta pantallas o layouts. Nada de hooks, estilos ni condiciones.
5. Un componente nace en `screens/<pantalla>/`. Cuando lo usa una segunda pantalla, se mueve a `domain/` (si sabe del
   negocio) o a `ui/` (si es genérico). Nunca se copia.
6. Una variante visual (primario/secundario, tono, tamaño) es una prop del mismo componente.

### 3.4 Convenciones de nombres e idioma

- **Vocabulario del negocio en español** (en la API, en entidades y en nombres de pantallas): `Planilla`, `Trabajador`,
  `Vale`, `Nomina`, `Negocio`, `Administrador`, `Comando`, `Mensaje`. Son las palabras del producto y de los comandos.
- **Piezas técnicas y de UI genérica en inglés**: `Button`, `Card`, `TextField`, `useQuery`, `http`, `tokens`.
- Rutas en español y kebab-case (`/planillas/nueva`), porque se ven en los deep links.
- Componentes en `PascalCase.tsx`, hooks en `useCamelCase.ts`, estilos en `Nombre.styles.ts` al lado del componente,
  pruebas en `Nombre.test.tsx` al lado del archivo probado, barriles `index.ts` por carpeta.
- Alias de TypeScript: `@/*` → `./src/*` (`import { Button } from '@/components/ui/buttons'`).

---

## 4. Estructura de carpetas y archivos

Convención: **todo componente con estilos tiene `Nombre.styles.ts` al lado** y toda carpeta de componentes tiene
`index.ts`. En el árbol se muestran explícitamente en `ui/` y se omiten en el resto para no repetir.

> Este es el árbol del plan. Lo implementado lo sigue con las diferencias de la tabla del inicio
> ("Diferencias entre este plan y lo implementado").

```
MoviContabilidad/
├── app/                                        # SOLO enrutamiento (expo-router)
│   ├── _layout.tsx                             # <AppProviders><RootStack/></AppProviders>
│   ├── +not-found.tsx                          # → NoEncontradaScreen
│   ├── (auth)/
│   │   ├── _layout.tsx                         # Stack sin encabezado
│   │   └── vincular.tsx                        # → VincularScreen
│   └── (app)/
│       ├── _layout.tsx                         # Stack con AppHeader; recorre appScreens
│       ├── index.tsx                           # → PrincipalScreen (ruta "/")
│       ├── ayuda.tsx                           # → AyudaScreen
│       ├── planillas/
│       │   ├── index.tsx                       # → PlanillasScreen
│       │   ├── nueva.tsx                       # → NuevaPlanillaScreen  (?fecha=&hoja=)
│       │   └── [planillaId]/
│       │       ├── index.tsx                   # → EdicionPlanillaScreen (?comando=&texto=)
│       │       └── resumen.tsx                 # → ResumenPlanillaScreen
│       ├── trabajadores/
│       │   ├── index.tsx                       # → TrabajadoresScreen
│       │   └── [trabajadorId]/
│       │       ├── index.tsx                   # → DetalleTrabajadorScreen
│       │       └── nominas/
│       │           └── [nominaId].tsx          # → DetalleNominaScreen
│       └── perfil/
│           ├── index.tsx                       # → PerfilScreen
│           ├── negocio.tsx                     # → EditarNegocioScreen
│           └── administrador.tsx               # → EditarAdministradorScreen
│
├── assets/
│   └── images/
│       ├── icon.png                            # ícono: libro esmeralda con filete dorado
│       ├── adaptive-icon-foreground.png
│       ├── adaptive-icon-monochrome.png
│       └── splash-icon.png
│
├── docs/
│   └── plan-app-movil.md                       # este documento
│
├── src/
│   ├── api/                                    # ÚNICA capa que conoce el backend
│   │   ├── index.ts                            # barril: endpoints + entidades + ApiError
│   │   ├── client/
│   │   │   ├── config.ts                       # API_URL (de EXPO_PUBLIC_API_URL), timeouts
│   │   │   ├── http.ts                         # request<T>(): ÚNICO fetch; Bearer; timeout; reintento tras refresh
│   │   │   ├── errors.ts                       # ApiError {status, codigo, message}; mensajes de red legibles
│   │   │   ├── tokens.ts                       # access/refresh en memoria + suscriptores
│   │   │   └── refresh.ts                      # refresco "single-flight" ante 401 + onSessionExpired
│   │   ├── endpoints/
│   │   │   ├── auth.api.ts                     # crearVinculacion, consultarVinculacion, refrescar, cerrarSesion
│   │   │   ├── perfil.api.ts                   # obtenerPerfil, actualizarNegocio, actualizarAdministrador
│   │   │   ├── comandos.api.ts                 # listarComandos
│   │   │   ├── planillas.api.ts                # listarMeses, listarDelMes, obtenerHoy, crearOAbrir, obtener, obtenerResumen
│   │   │   ├── mensajes.api.ts                 # obtenerEstadoChat, enviarMensaje, responderSeleccion, cancelarSeleccion
│   │   │   └── trabajadores.api.ts             # listarTrabajadores, obtenerTrabajador, obtenerNomina
│   │   ├── dto/                                # forma EXACTA del JSON del backend (snake_case)
│   │   │   ├── auth.dto.ts
│   │   │   ├── perfil.dto.ts
│   │   │   ├── comandos.dto.ts
│   │   │   ├── planillas.dto.ts
│   │   │   ├── mensajes.dto.ts
│   │   │   └── trabajadores.dto.ts
│   │   ├── entities/                           # tipos que usa la app (camelCase, fechas como Date)
│   │   │   ├── index.ts
│   │   │   ├── sesion.ts                       # Tokens, Vinculacion, EstadoVinculacion
│   │   │   ├── administrador.ts                # Administrador
│   │   │   ├── negocio.ts                      # Negocio, Perfil
│   │   │   ├── comando.ts                      # Comando, TipoArgumentos
│   │   │   ├── planilla.ts                     # Planilla, MesPlanillas, PlanillasDeHoy
│   │   │   ├── resumen-planilla.ts             # ResumenPlanilla, TotalesPlanilla, UsoSeccion
│   │   │   ├── mensaje.ts                      # Mensaje, TipoMensaje, AutorMensaje, Seleccion, OpcionSeleccion, EstadoChat
│   │   │   └── trabajador.ts                   # Trabajador, DetalleTrabajador, Vale, NominaArchivada
│   │   └── mappers/                            # dto → entidad (el ÚNICO lugar que conoce ambos)
│   │       ├── auth.mapper.ts
│   │       ├── perfil.mapper.ts
│   │       ├── comandos.mapper.ts
│   │       ├── planillas.mapper.ts
│   │       ├── mensajes.mapper.ts
│   │       └── trabajadores.mapper.ts
│   │
│   ├── storage/                                # SQLite LOCAL del teléfono (expo-sqlite): historial del chat
│   │   ├── index.ts
│   │   ├── database.ts                         # abre movicontabilidad.db, WAL, aplica migraciones
│   │   ├── migrations.ts                       # migraciones numeradas con PRAGMA user_version
│   │   └── chat/
│   │       ├── chatHistory.repository.ts       # guardar enviados y respuestas, listar por planilla, estado de envío
│   │       ├── chatHistory.types.ts            # fila de la tabla ⇄ entidad Mensaje
│   │       └── chatHistory.cleanup.ts          # borra mensajes de más de 90 días al abrir la app
│   │
│   ├── session/                                # patrón de ZoneUp + persistencia
│   │   ├── index.ts
│   │   ├── SessionProvider.tsx                 # estado: restaurando | sinSesion | conSesion
│   │   ├── useSession.ts
│   │   ├── session.storage.ts                  # refresh token en expo-secure-store; perfil en caché en expo-sqlite/kv-store
│   │   └── session.types.ts
│   │
│   ├── providers/
│   │   ├── index.ts
│   │   ├── AppProviders.tsx                    # compone todo en orden (ver §5.3)
│   │   ├── QueryProvider.tsx                   # QueryClient: reintentos, foco de la app, errores 401
│   │   └── SplashGate.tsx                      # mantiene el splash hasta tener fuentes + sesión restaurada
│   │
│   ├── navigation/
│   │   ├── index.ts
│   │   ├── RootStack.tsx                       # Stack raíz con Stack.Protected (guard + redirectTo)
│   │   ├── stackOptions.tsx                    # header (AppHeader), animación, fondo blanco
│   │   ├── appScreens.ts                       # ruta → título/opciones del grupo (app)
│   │   └── routes.ts                           # constructores de Href tipados: routes.planilla(id), …
│   │
│   ├── theme/
│   │   ├── index.ts                            # export const theme = { colors, typography, … }
│   │   ├── palette.ts                          # paleta cruda (esmeralda-50…900, dorado-…, neutros)
│   │   ├── colors.ts                           # tokens semánticos: text.primary, action.primary, border.subtle…
│   │   ├── typography.ts                       # variantes de texto (tamaño, alto de línea, peso, familia)
│   │   ├── fonts.ts                            # mapa de fuentes para useFonts
│   │   ├── spacing.ts                          # escala de 4 pt
│   │   ├── radii.ts
│   │   ├── shadows.ts
│   │   ├── sizes.ts                            # alto de controles, íconos, área táctil mínima (44)
│   │   └── tones.ts                            # tono → {fondo, borde, texto, ícono} (lo usan Badge, Banner, burbujas)
│   │
│   ├── hooks/
│   │   ├── data/                               # React Query: un hook por consulta o mutación
│   │   │   ├── queryKeys.ts
│   │   │   ├── perfil/
│   │   │   │   ├── usePerfil.ts
│   │   │   │   ├── useActualizarNegocio.ts
│   │   │   │   └── useActualizarAdministrador.ts
│   │   │   ├── comandos/
│   │   │   │   └── useComandos.ts              # staleTime infinito + catálogo de respaldo
│   │   │   ├── planillas/
│   │   │   │   ├── useMesesPlanillas.ts
│   │   │   │   ├── usePlanillasDelMes.ts       # enabled solo si el acordeón del mes está abierto
│   │   │   │   ├── usePlanillasDeHoy.ts
│   │   │   │   ├── usePlanilla.ts
│   │   │   │   ├── useResumenPlanilla.ts
│   │   │   │   └── useCrearPlanilla.ts
│   │   │   ├── mensajes/
│   │   │   │   ├── useHistorialChat.ts         # lee el SQLite local (paginado hacia atrás)
│   │   │   │   ├── useEstadoChat.ts            # GET /estado: pregunta pendiente y qué deshace 'deshacer'
│   │   │   │   ├── useEnviarMensaje.ts         # guarda local → POST → guarda respuestas; client_id idempotente
│   │   │   │   ├── useResponderSeleccion.ts
│   │   │   │   └── useCancelarSeleccion.ts
│   │   │   └── trabajadores/
│   │   │       ├── useTrabajadores.ts
│   │   │       ├── useTrabajador.ts
│   │   │       └── useNominaArchivada.ts
│   │   ├── screens/                            # un hook por pantalla: estado + acciones; la vista solo pinta
│   │   │   ├── vincular/useVincularScreen.ts
│   │   │   ├── principal/usePrincipalScreen.ts
│   │   │   ├── planillas/usePlanillasScreen.ts
│   │   │   ├── nueva-planilla/
│   │   │   │   ├── useNuevaPlanillaScreen.ts
│   │   │   │   └── useFechaHojaSincronizadas.ts  # texto ⇄ calendario ⇄ hoja disponible
│   │   │   ├── edicion-planilla/
│   │   │   │   ├── useEdicionPlanillaScreen.ts
│   │   │   │   ├── useComposer.ts              # máquina de estados del composer (§12)
│   │   │   │   ├── composer.reducer.ts         # reducer puro (fácil de probar)
│   │   │   │   └── useSugerenciasTrabajador.ts
│   │   │   ├── resumen-planilla/useResumenPlanillaScreen.ts
│   │   │   ├── trabajadores/useTrabajadoresScreen.ts
│   │   │   ├── detalle-trabajador/useDetalleTrabajadorScreen.ts
│   │   │   ├── detalle-nomina/useDetalleNominaScreen.ts
│   │   │   ├── perfil/usePerfilScreen.ts
│   │   │   ├── editar-negocio/useEditarNegocioScreen.ts
│   │   │   ├── editar-administrador/useEditarAdministradorScreen.ts
│   │   │   └── ayuda/useAyudaScreen.ts
│   │   └── shared/
│   │       ├── useAbrirEnGoogleSheets.ts
│   │       ├── useTecladoVisible.ts
│   │       ├── useValorDiferido.ts             # debounce
│   │       ├── useRefrescarAlEnfocar.ts        # refetch al volver a la pantalla
│   │       └── useSondeo.ts                    # polling (vinculación)
│   │
│   ├── utils/
│   │   ├── dates/
│   │   │   ├── fechaPlanilla.ts                # dd-mm-aaaa ⇄ Date, validación
│   │   │   ├── mascaraFecha.ts                 # "24112026" → "24-11-2026" mientras se escribe
│   │   │   ├── calendario.ts                   # matriz 6×7 del mes (semana empieza en lunes)
│   │   │   ├── meses.ts                        # "noviembre-2026" ⇄ {anio, mes} ⇄ "Noviembre 2026"
│   │   │   └── fechaRelativa.ts                # "Hoy", "Ayer", "lun 24 nov"
│   │   ├── money/
│   │   │   └── formatearMonto.ts               # 5000 → "$5.000" (mismo formato que format_amount del bot)
│   │   ├── text/
│   │   │   ├── normalizar.ts                   # sin tildes/mayúsculas (equivale a name_key del bot)
│   │   │   └── iniciales.ts
│   │   ├── planillas/
│   │   │   ├── ordinales.ts                    # 1 → "Primera", 2 → "Segunda"…; nombre "dd-mm-aaaa-N"
│   │   │   └── disponibilidadHojas.ts          # qué hojas se pueden abrir/crear para una fecha
│   │   └── linking/
│   │       ├── googleSheets.ts                 # app Sheets (iOS esquema / Android intent) con respaldo web
│   │       └── whatsapp.ts                     # https://wa.me/<numero>?text=…
│   │
│   ├── config/
│   │   └── env.ts                              # lee y valida EXPO_PUBLIC_*
│   │
│   ├── constants/
│   │   ├── app.ts                              # intervalos de sondeo, timeouts, máx. hojas en el selector
│   │   └── comandosRespaldo.ts                 # catálogo local si /app/comandos falla
│   │
│   └── components/
│       ├── ui/                                 # TRANSVERSALES: no saben nada del negocio
│       │   ├── typography/
│       │   │   ├── Text.tsx                    # variant: display|title|heading|body|bodyStrong|caption|overline|amount|amountLarge
│       │   │   ├── Text.styles.ts
│       │   │   └── index.ts
│       │   ├── buttons/
│       │   │   ├── Button.tsx                  # variant: primary|secondary|outline|ghost|danger · size: sm|md|lg
│       │   │   ├── Button.styles.ts
│       │   │   ├── IconButton.tsx              # variant: plain|tonal|outline
│       │   │   ├── IconButton.styles.ts
│       │   │   ├── ActionTile.tsx              # botón-tarjeta grande: ícono + título + subtítulo · variant: default|featured
│       │   │   ├── ActionTile.styles.ts
│       │   │   ├── FloatingActionButton.tsx
│       │   │   ├── FloatingActionButton.styles.ts
│       │   │   └── index.ts
│       │   ├── inputs/
│       │   │   ├── TextField.tsx               # label, ayuda, error, accesorios izq/der, multilinea
│       │   │   ├── TextField.styles.ts
│       │   │   ├── DateField.tsx               # TextField + máscara dd-mm-aaaa + teclado numérico
│       │   │   ├── SearchField.tsx             # TextField + lupa + limpiar
│       │   │   ├── FormField.tsx               # adaptador genérico de react-hook-form (render-prop)
│       │   │   └── index.ts
│       │   ├── selects/
│       │   │   ├── Dropdown.tsx                # opciones con disabled + descripción
│       │   │   ├── Dropdown.styles.ts
│       │   │   ├── DropdownOption.tsx
│       │   │   └── index.ts
│       │   ├── calendar/
│       │   │   ├── Calendar.tsx
│       │   │   ├── CalendarHeader.tsx          # mes + flechas
│       │   │   ├── CalendarWeekdays.tsx        # L M M J V S D
│       │   │   ├── CalendarDay.tsx             # seleccionado / hoy / fuera de mes / marcas
│       │   │   ├── Calendar.styles.ts
│       │   │   ├── calendar.types.ts           # CalendarProps, DayMarks
│       │   │   └── index.ts
│       │   ├── backgrounds/
│       │   │   ├── ScreenBackground.tsx        # variant: plain|hero|ledger (blanco puro siempre)
│       │   │   ├── patterns/
│       │   │   │   ├── LedgerLines.tsx         # renglones de libro contable al 3 % (fondo del chat)
│       │   │   │   └── HeroWatermark.tsx       # monograma gigante al 4 % (Principal, Vincular)
│       │   │   └── index.ts
│       │   ├── decorations/
│       │   │   ├── GoldDivider.tsx             # variant: line|short|ornament (línea–rombo–línea)
│       │   │   ├── GoldAccentBar.tsx           # barra de 2–3 px para destacar un bloque
│       │   │   └── index.ts
│       │   ├── layout/
│       │   │   ├── Screen.tsx                  # SafeArea + fondo + padding + scroll/refresh opcionales
│       │   │   ├── Screen.styles.ts
│       │   │   ├── Row.tsx                     # flex-row con gap por token
│       │   │   ├── Column.tsx
│       │   │   ├── Spacer.tsx
│       │   │   ├── Section.tsx                 # overline dorado + título + contenido
│       │   │   └── index.ts
│       │   ├── surfaces/
│       │   │   ├── Card.tsx                    # variant: outlined|elevated|tinted · onPress opcional
│       │   │   ├── Card.styles.ts
│       │   │   └── index.ts
│       │   ├── lists/
│       │   │   ├── ListItem.tsx                # leading, título, subtítulo, trailing, chevron
│       │   │   ├── ListItem.styles.ts
│       │   │   ├── Accordion.tsx               # cabecera + contenido animado; controlado o no
│       │   │   ├── Accordion.styles.ts
│       │   │   ├── SectionHeader.tsx
│       │   │   ├── ListSeparator.tsx
│       │   │   └── index.ts
│       │   ├── overlays/
│       │   │   ├── BottomSheet.tsx             # contenedor inferior genérico
│       │   │   ├── ActionSheet.tsx             # BottomSheet + lista de acciones
│       │   │   └── index.ts
│       │   ├── feedback/
│       │   │   ├── alert/
│       │   │   │   ├── AlertProvider.tsx       # (idea de ZoneUp) mostrar() y confirmar() con promesas
│       │   │   │   ├── AlertDialog.tsx
│       │   │   │   └── useAlert.ts
│       │   │   ├── toast/
│       │   │   │   ├── ToastProvider.tsx
│       │   │   │   ├── Toast.tsx
│       │   │   │   └── useToast.ts
│       │   │   ├── Banner.tsx                  # tone: info|success|warning|danger
│       │   │   ├── EmptyState.tsx
│       │   │   ├── ErrorState.tsx              # con "Reintentar"
│       │   │   ├── LoadingState.tsx
│       │   │   ├── Skeleton.tsx
│       │   │   ├── Spinner.tsx
│       │   │   └── index.ts
│       │   ├── badges/
│       │   │   ├── Badge.tsx                   # tone: neutral|success|warning|danger|gold
│       │   │   ├── Chip.tsx                    # seleccionable, ícono, disabled (banda, sugerencias, opciones)
│       │   │   └── index.ts
│       │   ├── avatars/
│       │   │   ├── Avatar.tsx                  # iniciales · variant: plain|monogram (aro dorado)
│       │   │   └── index.ts
│       │   ├── progress/
│       │   │   ├── ProgressBar.tsx             # valor/máximo; tono según ocupación
│       │   │   └── index.ts
│       │   ├── icons/
│       │   │   ├── Icon.tsx                    # <Icon name="gasto" size="md" tone="primary" />
│       │   │   ├── iconRegistry.ts             # nombre semántico → componente de lucide
│       │   │   └── index.ts
│       │   ├── gestures/
│       │   │   ├── TapArea.tsx                 # onPress / onDoubleTap / onLongPress (exclusivos, Pressable + temporizador)
│       │   │   └── index.ts
│       │   └── keyboard/
│       │       ├── DismissKeyboardArea.tsx     # tocar aquí oculta el teclado
│       │       ├── KeyboardAvoider.tsx         # KeyboardAvoidingView (padding, sin offset: ver §12.1)
│       │       ├── useKeyboardVisible.ts
│       │       └── index.ts
│       │
│       ├── navigation/
│       │   ├── AppHeader.tsx                   # título + subtítulo + filete dorado inferior
│       │   ├── HeaderBackButton.tsx
│       │   ├── HeaderActions.tsx               # fila de IconButton a la derecha
│       │   └── index.ts
│       │
│       ├── domain/                             # de NEGOCIO, usados por 2+ pantallas
│       │   ├── money/
│       │   │   ├── MoneyText.tsx               # "$5.000", cifras tabulares, rojo si es negativo
│       │   │   └── index.ts
│       │   ├── metrics/
│       │   │   ├── KpiTile.tsx                 # etiqueta + MoneyText (Principal, Resumen)
│       │   │   ├── KpiGrid.tsx
│       │   │   └── index.ts
│       │   ├── planillas/
│       │   │   ├── PlanillaRow.tsx             # "Lun 24 nov" + HojaBadge (Planillas, Principal)
│       │   │   ├── HojaBadge.tsx               # "Hoja 2"
│       │   │   └── index.ts
│       │   ├── trabajadores/
│       │   │   ├── ValeRow.tsx                 # fecha + monto (Detalle trabajador, Detalle nómina)
│       │   │   └── index.ts
│       │   └── estado/
│       │       ├── GoogleStatusBanner.tsx      # "El servidor no está conectado con Google" (Principal, Edición)
│       │       └── index.ts
│       │
│       └── screens/                            # UNA carpeta por pantalla
│           ├── vincular/
│           │   ├── VincularScreen.tsx
│           │   ├── CodigoVinculacion.tsx       # 6 dígitos grandes enmarcados en dorado
│           │   ├── PasosVinculacion.tsx        # 1. Abre WhatsApp 2. Envía 3. Listo
│           │   ├── EstadoVinculacion.tsx       # esperando / expirado (generar otro)
│           │   └── index.ts
│           ├── principal/
│           │   ├── PrincipalScreen.tsx
│           │   ├── EncabezadoNegocio.tsx       # monograma + nombre del negocio + saludo + fecha
│           │   ├── TarjetaHoy.tsx              # planilla de hoy: KPIs + "Continuar" / "Crear la de hoy"
│           │   ├── AccionesPrincipales.tsx     # grilla de ActionTile
│           │   └── index.ts
│           ├── planillas/
│           │   ├── PlanillasScreen.tsx
│           │   ├── ListaMeses.tsx
│           │   ├── MesPlanillas.tsx            # Accordion de un mes; carga perezosa al abrir
│           │   ├── FilaPlanillaInteractiva.tsx # TapArea + PlanillaRow (toque / doble toque / mantener)
│           │   ├── AccionesPlanillaSheet.tsx   # ActionSheet al mantener presionado
│           │   ├── PistaDobleToque.tsx         # Banner que se muestra hasta que el usuario lo cierra
│           │   └── index.ts
│           ├── nueva-planilla/
│           │   ├── NuevaPlanillaScreen.tsx
│           │   ├── SelectorFechaHoja.tsx       # DateField + Dropdown en una fila
│           │   ├── CalendarioPlanillas.tsx     # Calendar con marcas de planillas existentes
│           │   ├── AvisoSaldoInicial.tsx       # de dónde saldrá el saldo de caja (B42)
│           │   └── index.ts
│           ├── edicion-planilla/
│           │   ├── EdicionPlanillaScreen.tsx
│           │   ├── encabezado/
│           │   │   ├── TituloPlanilla.tsx      # "24-11-2026 · Hoja 2" + negocio
│           │   │   └── AccionesEncabezado.tsx  # Resumen · Abrir en Sheets
│           │   ├── chat/
│           │   │   ├── ListaMensajes.tsx       # FlatList invertida + paginación hacia atrás
│           │   │   ├── BurbujaMensaje.tsx      # propia / bot por tono / estado de envío
│           │   │   ├── TextoConComando.tsx     # "Gasto:" en esmeralda + resto del texto
│           │   │   ├── OpcionesSeleccion.tsx   # opciones del menú como Chips + "Cancelar"
│           │   │   ├── SeparadorDia.tsx
│           │   │   ├── IndicadorProcesando.tsx # "Registrando…" mientras responde el bot
│           │   │   ├── ChatVacio.tsx
│           │   │   └── index.ts
│           │   ├── composer/
│           │   │   ├── Composer.tsx            # fila: PrefijoComando + TextInput + BotonEnviar
│           │   │   ├── PrefijoComando.tsx
│           │   │   ├── BotonEnviar.tsx
│           │   │   └── index.ts
│           │   ├── banda/
│           │   │   ├── BandaComandos.tsx       # una línea, scroll horizontal, siempre visible
│           │   │   └── index.ts
│           │   ├── sugerencias/
│           │   │   ├── SugerenciasTrabajador.tsx  # chips de nombres para Préstamo / Nómina
│           │   │   └── index.ts
│           │   └── index.ts
│           ├── resumen-planilla/
│           │   ├── ResumenPlanillaScreen.tsx
│           │   ├── TotalesPlanilla.tsx         # KpiGrid con B38, B39, B40, B42, B58
│           │   ├── UsoSecciones.tsx            # ProgressBar por sección (gastos 12/24, aseo 8/8…)
│           │   └── index.ts
│           ├── trabajadores/
│           │   ├── TrabajadoresScreen.tsx
│           │   ├── ListaTrabajadores.tsx
│           │   ├── FilaTrabajador.tsx
│           │   └── index.ts
│           ├── detalle-trabajador/
│           │   ├── DetalleTrabajadorScreen.tsx
│           │   ├── EncabezadoTrabajador.tsx
│           │   ├── PeriodoActual.tsx           # total + vales usados X/16
│           │   ├── ListaVales.tsx
│           │   ├── ListaNominas.tsx
│           │   ├── AccionesTrabajador.tsx      # Prestar · Pagar nómina · Abrir en Sheets
│           │   └── index.ts
│           ├── detalle-nomina/
│           │   ├── DetalleNominaScreen.tsx
│           │   └── index.ts
│           ├── perfil/
│           │   ├── PerfilScreen.tsx
│           │   ├── TarjetaNegocio.tsx
│           │   ├── TarjetaAdministrador.tsx
│           │   ├── ListaAdministradores.tsx
│           │   └── index.ts
│           ├── editar-negocio/
│           │   ├── EditarNegocioScreen.tsx
│           │   └── index.ts
│           ├── editar-administrador/
│           │   ├── EditarAdministradorScreen.tsx
│           │   └── index.ts
│           ├── ayuda/
│           │   ├── AyudaScreen.tsx
│           │   ├── TarjetaComando.tsx
│           │   └── index.ts
│           └── no-encontrada/
│               ├── NoEncontradaScreen.tsx
│               └── index.ts
│
├── .env.example                                # EXPO_PUBLIC_API_URL=https://contabilidad.notiasis.com
├── app.json
├── eas.json                                    # perfiles development / preview / production
├── eslint.config.js                            # reglas de capas (§3.3)
├── jest.config.js
├── package.json
└── tsconfig.json                               # "@/*": ["./src/*"]
```

Se borran de la plantilla actual: `app/(tabs)/`, `app/modal.tsx`, `app/+html.tsx`, `components/` (raíz),
`constants/Colors.ts` y `assets/fonts/SpaceMono-Regular.ttf`.

---

## 5. Navegación (stack)

### 5.1 Mapa

```
            (auth)                                   (app) — un solo Stack
        ┌──────────┐   vinculada   ┌────────────┐
        │ Vincular │ ────────────▶ │ Principal  │
        └──────────┘               └─────┬──────┘
                                         │
      ┌───────────────┬──────────────────┼──────────────────┬──────────────┬────────┐
      ▼               ▼                  ▼                  ▼              ▼        ▼
 Nueva planilla  Nueva planilla     Planillas          Trabajadores     Perfil    Ayuda
 (hoja 1)        (hoja siguiente)      │                    │             │
      │               │          toque │ doble toque        ▼             ├─▶ Editar negocio
      └───replace─────┴────▶ Edición ◀─┘ └─▶ Google Sheets  Detalle       └─▶ Editar administrador
                               │                            trabajador
                               ▼                              │   │
                            Resumen                           │   └─▶ Detalle nómina
                                                              └─ Prestar / Pagar nómina ─▶ Edición (de hoy)
```

### 5.2 Rutas y parámetros

| Ruta | Pantalla | Parámetros |
|---|---|---|
| `/vincular` | Vincular | — |
| `/` | Principal | — |
| `/planillas` | Planillas | — |
| `/planillas/nueva` | Nueva planilla | `fecha?` (dd-mm-aaaa), `hoja?` (`1`, `2`, … o `siguiente`) |
| `/planillas/[planillaId]` | Edición | `comando?`, `texto?` (para abrir con un comando preseleccionado) |
| `/planillas/[planillaId]/resumen` | Resumen | — |
| `/trabajadores` | Trabajadores | — |
| `/trabajadores/[trabajadorId]` | Detalle trabajador | — |
| `/trabajadores/[trabajadorId]/nominas/[nominaId]` | Detalle nómina | — |
| `/perfil` | Mi perfil | — |
| `/perfil/negocio` | Editar negocio | — |
| `/perfil/administrador` | Editar administrador | — |
| `/ayuda` | Ayuda | — |

Nunca se escriben rutas a mano en los componentes: se usa `src/navigation/routes.ts`.

```ts
// src/navigation/routes.ts
export const routes = {
  principal: '/',
  vincular: '/vincular',
  planillas: '/planillas',
  nuevaPlanilla: (p?: { fecha?: string; hoja?: number | 'siguiente' }) =>
    ({ pathname: '/planillas/nueva', params: p ?? {} }) as const,
  planilla: (planillaId: string, p?: { comando?: string; texto?: string }) =>
    ({ pathname: '/planillas/[planillaId]', params: { planillaId, ...p } }) as const,
  resumenPlanilla: (planillaId: string) =>
    ({ pathname: '/planillas/[planillaId]/resumen', params: { planillaId } }) as const,
  trabajadores: '/trabajadores',
  trabajador: (trabajadorId: string) =>
    ({ pathname: '/trabajadores/[trabajadorId]', params: { trabajadorId } }) as const,
  nomina: (trabajadorId: string, nominaId: number) =>
    ({ pathname: '/trabajadores/[trabajadorId]/nominas/[nominaId]',
       params: { trabajadorId, nominaId: String(nominaId) } }) as const,
  perfil: '/perfil',
  editarNegocio: '/perfil/negocio',
  editarAdministrador: '/perfil/administrador',
  ayuda: '/ayuda',
} satisfies Record<string, Href | ((...args: never[]) => Href)>;
```

### 5.3 Layouts (completos: no llevan más que esto)

```tsx
// app/_layout.tsx
import { AppProviders } from '@/providers';
import { RootStack } from '@/navigation';

export default function RootLayout() {
  return (
    <AppProviders>
      <RootStack />
    </AppProviders>
  );
}
```

```tsx
// app/(app)/_layout.tsx
import { Stack } from 'expo-router';
import { appScreens, appStackOptions } from '@/navigation';

export default function AppLayout() {
  return (
    <Stack screenOptions={appStackOptions}>
      {appScreens.map(({ name, options }) => (
        <Stack.Screen key={name} name={name} options={options} />
      ))}
    </Stack>
  );
}
```

```tsx
// app/(auth)/_layout.tsx
import { Stack } from 'expo-router';
import { authStackOptions } from '@/navigation';

export default function AuthLayout() {
  return <Stack screenOptions={authStackOptions} />;
}
```

```tsx
// app/(app)/planillas/[planillaId]/index.tsx   ← así son TODOS los archivos de ruta
export { default } from '@/components/screens/edicion-planilla';
```

Lo que el layout no hace, lo hacen estos archivos de `src/`:

```tsx
// src/navigation/RootStack.tsx  (idea de ZoneUp: las rutas privadas no existen sin sesión)
export function RootStack() {
  const { estado } = useSession();
  const conSesion = estado === 'conSesion';
  return (
    <Stack screenOptions={rootStackOptions}>
      <Stack.Protected guard={conSesion} redirectTo={routes.vincular}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
      <Stack.Protected guard={!conSesion} redirectTo={routes.principal}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );
}
```

Mientras la sesión se restaura (`restaurando`), `SplashGate` mantiene el splash, así que no se ve la vinculación.

```ts
// src/navigation/appScreens.ts
export const appScreens = [
  { name: 'index', options: { headerShown: false } },   // Principal
  { name: 'planillas/index', options: { title: 'Planillas' } },
  { name: 'planillas/nueva', options: { title: 'Nueva planilla' } },
  { name: 'planillas/[planillaId]/index', options: { title: 'Planilla' } },   // el título real lo pone la pantalla
  { name: 'planillas/[planillaId]/resumen', options: { title: 'Resumen' } },
  { name: 'trabajadores/index', options: { title: 'Trabajadores' } },
  { name: 'trabajadores/[trabajadorId]/index', options: { title: 'Trabajador' } },
  { name: 'trabajadores/[trabajadorId]/nominas/[nominaId]', options: { title: 'Nómina' } },
  { name: 'perfil/index', options: { title: 'Mi perfil' } },
  { name: 'perfil/negocio', options: { title: 'Editar negocio' } },
  { name: 'perfil/administrador', options: { title: 'Editar administrador' } },
  { name: 'ayuda', options: { title: 'Ayuda' } },
] as const;
```

```tsx
// src/providers/AppProviders.tsx — orden de afuera hacia adentro
<SafeAreaProvider>
  <StatusBar style="dark" />
  <QueryProvider>                 // React Query
    <AlertProvider>
      <ToastProvider>
        <SessionProvider>         // usa QueryClient (limpiar al salir) y alertas (sesión vencida)
          <SplashGate>            // fuentes + sesión restaurada + SQLite listo → oculta el splash
            {children}
```

Reglas de navegación:

- Tras crear/abrir una planilla desde "Nueva planilla" se usa `router.replace` (atrás vuelve a donde estaba el
  usuario, no al formulario).
- Al vincular o cerrar sesión no se navega a mano: el cambio de `estado` hace que `Stack.Protected` muestre el grupo
  correcto (igual que ZoneUp).
- Los títulos dinámicos (nombre de la planilla, del trabajador) los pone la pantalla con
  `<Stack.Screen options={{ title }} />` dentro de su componente, nunca el archivo de ruta.

---

## 6. Autenticación en la app

```ts
// src/session/session.types.ts
export type EstadoSesion = 'restaurando' | 'sinSesion' | 'conSesion';

export interface Session {
  estado: EstadoSesion;
  perfil: Perfil | null;                       // administrador + negocio + hoy + google_conectado
  iniciarVinculacion(): Promise<Vinculacion>;  // POST /app/auth/vinculaciones
  esperarVinculacion(v: Vinculacion, signal: AbortSignal): Promise<void>;  // sondeo hasta confirmada
  cerrarSesion(): Promise<void>;               // nunca falla: aunque no haya red, sale igual
  actualizarPerfil(p: Perfil): void;
}
```

| Momento | Qué pasa |
|---|---|
| Abrir la app | `SplashGate` mantiene el splash. `SessionProvider` lee el refresh de SecureStore: si no hay → `sinSesion`. Si hay → `POST /app/auth/refresh` → guarda el nuevo refresh → `GET /app/perfil` → `conSesion`. 401 → borra todo → `sinSesion`. Sin red → `conSesion` con el perfil guardado y banner "Sin conexión" |
| Vincular | La pantalla pide la vinculación, muestra el código, abre WhatsApp y sondea cada 2 s. Al confirmarse: tokens a `tokens.ts`, refresh a SecureStore, perfil al estado → `conSesion` |
| Petición con 401 | `http.ts` llama a `refresh.ts` (una sola vez aunque fallen 5 peticiones a la vez), reintenta una vez. Si el refresh falla → `onSessionExpired` → `SessionProvider` pasa a `sinSesion` y muestra "Tu sesión expiró, vincula la app de nuevo" |
| Cerrar sesión | `POST /app/auth/logout` (sin esperar si no hay red) → borra SecureStore → `queryClient.clear()` → `sinSesion` |
| Administrador desactivado por CLI | El backend responde 401 → mismo camino que "sesión expirada" |

---

## 7. Capa de datos

```ts
// src/api/client/http.ts  (sesión y reintento; el único fetch está en transport.ts)
export async function request<T>(path: string, init?: {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  timeoutMs?: number;          // 30 s por defecto; 150 s para enviar mensajes
  auth?: boolean;              // false en /app/auth/*
  signal?: AbortSignal;
}): Promise<T>
```

- Errores: `ApiError` con `status`, `codigo` y `message` legible. Sin respuesta → "No se pudo conectar con el
  servidor. Revisa tu conexión." (status 0).
- Cada `endpoints/*.api.ts` llama a `request<Dto>()` y devuelve `mapper(dto)`: las pantallas nunca ven un DTO.

Claves de React Query (`src/hooks/data/queryKeys.ts`):

```ts
export const queryKeys = {
  perfil: ['perfil'],
  comandos: ['comandos'],
  planillas: {
    meses: ['planillas', 'meses'],
    delMes: (anio: number, mes: number) => ['planillas', 'mes', anio, mes],
    hoy: ['planillas', 'hoy'],
    detalle: (id: string) => ['planillas', id],
    resumen: (id: string) => ['planillas', id, 'resumen'],
    mensajes: (id: string) => ['planillas', id, 'mensajes'],
  },
  trabajadores: {
    lista: ['trabajadores'],
    detalle: (id: string) => ['trabajadores', id],
    nomina: (id: string, hojaId: number) => ['trabajadores', id, 'nominas', hojaId],
  },
} as const;
```

Invalidaciones:

| Acción | Invalida |
|---|---|
| Crear/abrir planilla | `meses`, `delMes(fecha)`, `hoy` |
| Enviar mensaje | `chat.historial(id)` (local), `chat.estado(id)`, `resumen(id)`, `hoy`; si el comando fue `trabajador`, `nomina` o `retiro` → `trabajadores.*` |
| Editar negocio/administrador | `perfil` |
| Cerrar sesión | todo (`queryClient.clear()`) |

`staleTime`: comandos ∞ · perfil 5 min · meses 1 min · mes 30 s · hoy 30 s · resumen 15 s · trabajadores 1 min.

---

### 7.1 Historial del chat en el teléfono (`src/storage/`)

**Decisión:** el historial se guarda solo en el SQLite local de cada teléfono (`expo-sqlite`). El servidor no guarda
mensajes: ejecuta, responde y olvida (salvo la respuesta en memoria por una hora para reintentos, §2.5).

Esquema local (`migrations.ts`, versión 1):

```sql
CREATE TABLE mensajes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  administrador_id INTEGER NOT NULL,      -- si otro administrador vincula el mismo teléfono, no ve lo ajeno
  planilla_id TEXT NOT NULL,
  client_id TEXT,                         -- solo mensajes propios
  autor TEXT NOT NULL CHECK (autor IN ('yo', 'bot')),
  comando TEXT,                           -- comando elegido en la banda (o NULL = "Libre")
  texto TEXT NOT NULL,
  tipo TEXT NOT NULL,                     -- enviado | exito | aviso | error | info | seleccion
  estado_envio TEXT,                      -- enviando | enviado | fallido (solo propios)
  responde_a TEXT,                        -- client_id del mensaje propio que originó la respuesta
  creado_en INTEGER NOT NULL              -- milisegundos Unix
);
CREATE INDEX idx_mensajes_planilla ON mensajes (administrador_id, planilla_id, id);
CREATE UNIQUE INDEX idx_mensajes_client ON mensajes (client_id) WHERE client_id IS NOT NULL;
```

Flujo de un envío (`useEnviarMensaje`):

1. Inserta el mensaje propio con `estado_envio = 'enviando'` y un `client_id` nuevo (UUID). Aparece al instante.
2. `POST /app/planillas/{id}/mensajes`.
3. Éxito → `estado_envio = 'enviado'` e inserta cada respuesta del bot (`autor = 'bot'`, `responde_a = client_id`)
   en una sola transacción. Guarda `estado` en la caché de React Query (`chat.estado`).
4. Error → `estado_envio = 'fallido'`. "Reintentar" reusa el mismo `client_id` solo si pasó menos de una hora;
   después muestra "No sabemos si quedó registrado: revisa el Resumen antes de enviarlo de nuevo".
5. Al abrir la app, los mensajes que quedaron `enviando` (la app se cerró a mitad) pasan a `fallido`.

React Query también maneja estos datos locales: `queryKey: ['chat', planillaId, 'historial']` con un `queryFn`
que lee el SQLite, e invalidación tras cada escritura. Así todas las pantallas leen datos con el mismo patrón.

Ciclo de vida:

- El historial se filtra por `administrador_id` de la sesión.
- Cerrar sesión **no** borra el historial (si el mismo administrador vuelve a vincular, lo recupera). Mi perfil tiene
  "Borrar historial del chat en este teléfono" (con confirmación).
- Al abrir la app se borran los mensajes de más de 90 días (`chatHistory.cleanup.ts`).

## 8. Sistema de diseño

### 8.1 Esquema

**Claro únicamente** (`userInterfaceStyle: "light"`), con estética de **libro contable elegante**: papel blanco,
tinta negra, acciones en esmeralda y filetes dorados. Los tokens están separados en paleta cruda y colores
semánticos, así que un modo oscuro futuro solo agrega otro `colors.ts`.

### 8.2 Opinión sobre los colores propuestos

La combinación funciona muy bien para contabilidad: el esmeralda se asocia con dinero y "todo en orden", el dorado da
un toque de calidad sin ser llamativo, y el negro y el gris sobre blanco puro dan la mejor legibilidad posible.
Ajustes necesarios:

1. **El dorado no sirve para texto pequeño sobre blanco.** Un dorado metálico (#C9A227) tiene contraste 2,4:1 (el
   mínimo para texto es 4,5:1). Por eso el dorado se usa en **decoración** (filetes, aros, puntos, bordes activos) y,
   cuando tiene que ser texto, se usa un **dorado oscuro** (#8A6A10, 5,1:1).
2. **Poco dorado.** Si cubre más del ~5 % de la pantalla se ve recargado. Es la firma, no el relleno.
3. **El esmeralda es el único color de acción.** Botones, chip activo, comando seleccionado, enlaces. Así el usuario
   aprende "verde = puedo tocar".
4. **Los montos van en negro, no en verde/rojo.** Pintar ingresos de verde y gastos de rojo convierte la pantalla en un
   árbol de Navidad. Solo un saldo **negativo** va en rojo.
5. **Hacen falta colores de estado** que no choquen con la marca: rojo para errores y ámbar quemado para avisos
   (distinto del dorado y siempre con ícono). Nunca solo color: también ícono o texto (daltonismo rojo/verde).

### 8.3 Paleta

| Token | Hex | Uso | Contraste sobre blanco |
|---|---|---|---|
| `blanco` | `#FFFFFF` | Fondo de todas las pantallas | — |
| `neutro-50` | `#F6F7F6` | Superficies: campos, burbujas del bot, tarjetas tintadas | — |
| `neutro-100` | `#ECEEEC` | Separadores suaves, skeleton | — |
| `neutro-200` | `#DDE1DE` | Bordes de tarjetas, campos y chips | — |
| `neutro-400` | `#8B928E` | Placeholder, deshabilitado | 3,2:1 (solo texto grande/no esencial) |
| `neutro-600` | `#5F6661` | **Texto secundario** (subtítulos, fechas, ayudas) | 5,9:1 ✅ |
| `neutro-800` | `#2C312E` | Texto fuerte alternativo | 13,2:1 ✅ |
| `tinta` | `#121614` | **Texto principal y montos** | 18,3:1 ✅ |
| `esmeralda-50` | `#EEF8F3` | Fondo de íconos de acción, éxito suave | — |
| `esmeralda-100` | `#D3EFE2` | **Burbuja propia del chat** | — |
| `esmeralda-300` | `#7CC9A6` | Bordes de foco, progreso | — |
| `esmeralda-500` | `#1F9D6E` | Íconos grandes, barras de progreso | 3,4:1 (solo gráficos) |
| `esmeralda-700` | `#0B6E4F` | **Primario**: botones, chip activo, prefijo del comando | 6,3:1 ✅ |
| `esmeralda-800` | `#085A41` | Primario presionado, prefijo en burbuja enviada | 8,2:1 ✅ |
| `esmeralda-900` | `#063F2E` | Títulos sobre fondos esmeralda claros | 11,9:1 ✅ |
| `dorado-50` | `#FBF6E8` | Fondo de la pista/aviso destacado | — |
| `dorado-100` | `#F4E7C3` | Fondo del código de vinculación | — |
| `dorado-300` | `#E3C677` | Filetes sobre fondos claros tintados | — |
| `dorado-500` | `#C9A227` | **Decoración**: filete del encabezado, aro del monograma, borde del chip activo, "hoy" en el calendario | 2,4:1 (nunca texto) |
| `dorado-600` | `#A8841A` | Íconos dorados, puntos de "hay planilla" | 3,5:1 (gráficos) |
| `dorado-700` | `#8A6A10` | **Texto dorado**: sobrelíneas de sección ("PLANILLA DE HOY") | 5,1:1 ✅ |
| `error-700` | `#B42318` | Errores, saldos negativos | 6,6:1 ✅ |
| `error-50` | `#FEF3F2` | Fondo de error | — |
| `aviso-700` | `#B54708` | Avisos ("sección llena") | 5,4:1 ✅ |
| `aviso-50` | `#FFFAEB` | Fondo de aviso | — |

Tokens semánticos (`src/theme/colors.ts`), lo único que importan los componentes:

```ts
export const colors = {
  background: { screen: palette.blanco, surface: palette.neutro50, sunken: palette.neutro100 },
  text: { primary: palette.tinta, secondary: palette.neutro600, muted: palette.neutro400,
          inverse: palette.blanco, gold: palette.dorado700, action: palette.esmeralda700 },
  border: { subtle: palette.neutro100, default: palette.neutro200, focus: palette.esmeralda300,
            gold: palette.dorado500 },
  action: { primary: palette.esmeralda700, primaryPressed: palette.esmeralda800,
            primarySoft: palette.esmeralda50 },
  decoration: { gold: palette.dorado500, goldSoft: palette.dorado100, goldIcon: palette.dorado600 },
  chat: { ownBubble: palette.esmeralda100, botBubble: palette.neutro50, commandPrefix: palette.esmeralda700,
          ownCommandPrefix: palette.esmeralda800 },
  status: {
    success: { fg: palette.esmeralda700, bg: palette.esmeralda50, accent: palette.esmeralda500 },
    warning: { fg: palette.aviso700, bg: palette.aviso50, accent: palette.aviso700 },
    danger:  { fg: palette.error700, bg: palette.error50, accent: palette.error700 },
    info:    { fg: palette.neutro600, bg: palette.neutro50, accent: palette.neutro400 },
  },
} as const;
```

### 8.4 Dónde va el dorado (lista cerrada)

- Filete de 1 px debajo de cada encabezado (`AppHeader`).
- Aro del monograma del negocio (Principal) y del avatar del trabajador.
- Borde de 1 px del chip de comando seleccionado (relleno esmeralda + borde dorado).
- Anillo del día "hoy" y puntos de "hay planilla" en el calendario.
- Sobrelíneas de sección en mayúsculas (`overline`, en `dorado-700`).
- Ornamento línea–rombo–línea en la pantalla de Vincular y en estados vacíos.
- Marco del código de vinculación.

### 8.5 Tipografía

| Variante | Fuente | Tamaño / línea | Uso |
|---|---|---|---|
| `display` | Playfair Display SemiBold | 30 / 36 | Nombre del negocio, título de Vincular |
| `title` | Inter SemiBold | 22 / 28 | Títulos de pantalla grandes |
| `heading` | Inter SemiBold | 17 / 24 | Títulos de tarjeta y sección |
| `body` | Inter Regular | 15 / 22 | Texto general, burbujas |
| `bodyStrong` | Inter Medium | 15 / 22 | Énfasis, filas de lista |
| `caption` | Inter Regular | 13 / 18 | Fechas, ayudas (neutro-600) |
| `overline` | Inter SemiBold, mayúsculas, espaciado 1,2 | 11 / 16 | Sobrelíneas (dorado-700) |
| `amount` | Inter SemiBold, cifras tabulares | 17 / 24 | Montos en listas |
| `amountLarge` | Inter Bold, cifras tabulares | 28 / 34 | KPIs |

Cifras tabulares (`fontVariant: ['tabular-nums']`) en todos los montos para que las columnas queden alineadas.

### 8.6 Espaciado, radios, sombras, íconos

- Espaciado (4 pt): `xxs 2 · xs 4 · sm 8 · md 12 · lg 16 · xl 24 · 2xl 32 · 3xl 48`. Margen lateral de pantalla: 20.
- Radios: `sm 8 · md 12 · lg 16 · xl 20 · pill 999`. Tarjetas 16, campos 12, chips pill, burbujas 18 (con la
  esquina de la "cola" en 4).
- Sombras: casi ninguna. Sobre blanco puro separan mejor los **bordes** `neutro-200`. Solo el FAB y las hojas
  inferiores llevan sombra suave (opacidad 0,08).
- Íconos: lucide, trazo 1,75, tamaños `sm 16 · md 20 · lg 24 · xl 28`. Área táctil mínima 44 × 44.
- Íconos por comando (`iconRegistry.ts`): gasto `ShoppingCart`, efectivo `Banknote`, saldo `Wallet`, préstamo
  `HandCoins`, retiro `ArrowUpFromLine`, aseo `SprayCan`, alimentación `UtensilsCrossed`, vale admin `UserRound`,
  inversión `TrendingUp`, nómina `BadgeDollarSign`, resumen `ClipboardList`, deshacer `Undo2`, corregir saldos
  `RefreshCcw`, libre `PenLine`.

---

## 9. Catálogo de componentes

Props principales (las de accesibilidad y `style`/`testID` se asumen en todos).

### 9.1 `ui/`

| Componente | Props clave | Notas |
|---|---|---|
| `Text` | `variant`, `tone` (`primary`/`secondary`/`muted`/`gold`/`action`/`inverse`/`danger`), `align`, `numberOfLines` | Único componente de texto de la app |
| `Button` | `label`, `onPress`, `variant`, `size`, `icon`, `iconPosition`, `loading`, `disabled`, `fullWidth` | `danger` para cerrar sesión; `ghost` reemplaza al "botón enlace" |
| `IconButton` | `icon`, `onPress`, `variant`, `size`, `accessibilityLabel` (obligatorio) | Encabezados, cerrar, enviar |
| `ActionTile` | `icon`, `title`, `subtitle`, `onPress`, `variant` | Grilla de Principal. `featured` = relleno esmeralda + filete dorado |
| `FloatingActionButton` | `icon`, `label?`, `onPress` | "+" en Planillas |
| `TextField` | `label`, `value`, `onChangeText`, `helper`, `error`, `leading`, `trailing`, `multiline` | Base de todos los campos |
| `DateField` | `value`, `onChange`, `error` | Máscara y teclado numérico; valida con `utils/dates` |
| `SearchField` | `value`, `onChange`, `placeholder` | Trabajadores |
| `FormField` | `control`, `name`, `rules`, `render` | Conecta react-hook-form con **cualquier** input (ZoneUp lo ataba a `TextInput`) |
| `Dropdown<T>` | `value`, `options: {value, label, description?, disabled?}[]`, `onChange`, `label` | Selector de hoja |
| `Calendar` | `month`, `selected`, `onSelect`, `onMonthChange`, `marks: Record<dd-mm-aaaa, number>`, `today` | Lógica pura en `utils/dates/calendario.ts` |
| `ScreenBackground` | `variant` | Siempre blanco; `hero` y `ledger` agregan patrón al 3–4 % |
| `GoldDivider` | `variant`, `inset` | |
| `GoldAccentBar` | `orientation`, `length` | |
| `Screen` | `scroll`, `refreshing`, `onRefresh`, `padded`, `background`, `footer` | Toda pantalla empieza con `Screen` |
| `Row` / `Column` | `gap`, `align`, `justify`, `wrap` | Gaps por token, nunca números sueltos |
| `Section` | `overline`, `title`, `action` | |
| `Card` | `variant`, `onPress`, `padding` | |
| `ListItem` | `leading`, `title`, `subtitle`, `trailing`, `chevron`, `onPress` | |
| `Accordion` | `title`, `subtitle`, `expanded`, `onToggle`, `children` | Meses de Planillas, nóminas del trabajador |
| `BottomSheet` / `ActionSheet` | `visible`, `onClose`, `actions: {icon, label, onPress, tone?}[]` | |
| `AlertProvider` / `useAlert` | `mostrar({tipo, titulo, mensaje})`, `confirmar({titulo, mensaje, destructiva})` | Promesas, en cola (idea de ZoneUp) |
| `ToastProvider` / `useToast` | `show({tone, message})` | Confirmaciones breves ("Enlace copiado") |
| `Banner` | `tone`, `title`, `message`, `action`, `onDismiss` | |
| `EmptyState` / `ErrorState` / `LoadingState` / `Skeleton` / `Spinner` | `icon`, `title`, `message`, `action` | Mismo aspecto en todas las pantallas |
| `Badge` | `tone`, `label`, `icon` | |
| `Chip` | `label`, `icon`, `selected`, `disabled`, `onPress`, `tone` | Se usa en banda, sugerencias y opciones de menú |
| `Avatar` | `name`, `size`, `variant` | |
| `ProgressBar` | `value`, `max`, `tone?` | Tono automático: >75 % aviso, 100 % peligro |
| `Icon` | `name`, `size`, `tone` | |
| `TapArea` | `onPress`, `onDoubleTap`, `onLongPress`, `children` | Gestos exclusivos: el toque simple espera ~250 ms por si llega el segundo |
| `DismissKeyboardArea` | `children` | |
| `KeyboardStickyFooter` | `children` | |

### 9.2 `navigation/`

| Componente | Props |
|---|---|
| `AppHeader` | `title`, `subtitle`, `back`, `actions` (lo conecta `stackOptions.header`) |
| `HeaderBackButton` | `onPress` |
| `HeaderActions` | `actions: {icon, label, onPress}[]` |

### 9.3 `domain/`

| Componente | Props | Usado en |
|---|---|---|
| `MoneyText` | `value`, `variant` (`amount`/`amountLarge`), `signed?` | Principal, Resumen, Trabajador, Nómina |
| `KpiTile` / `KpiGrid` | `label`, `value`, `hint?` | Principal, Resumen |
| `PlanillaRow` | `planilla`, `showDate?` | Planillas, Principal |
| `HojaBadge` | `hoja` | Planillas, Nueva, Edición |
| `ValeRow` | `vale` | Detalle trabajador, Detalle nómina |
| `GoogleStatusBanner` | `conectado` | Principal, Edición |

---

## 10. Pantallas

Formato: **ruta · componente · hook** — contenido de arriba hacia abajo — estados — acciones — extras.

### 10.1 Vincular (nueva, obligatoria)

`/vincular` · `VincularScreen` · `useVincularScreen`

- Fondo `hero` con marca de agua; título en `display`: "Bot Contabilidad"; texto "Conecta la app con tu WhatsApp".
- `GoldDivider ornament`.
- `PasosVinculacion`: 1) Toca "Abrir WhatsApp" 2) Envía el mensaje sin cambiarlo 3) Vuelve aquí.
- `CodigoVinculacion`: el código en grande dentro de un marco `dorado-100` (por si el usuario prefiere escribirlo a
  mano) + "Vence en 4:32".
- Botón primario "Abrir WhatsApp" → `whatsapp_url`.
- `EstadoVinculacion`: "Esperando confirmación…" (spinner) / "El código venció" + "Generar otro".
- Estados: creando, esperando, confirmada (transición automática), expirada, error de red.
- Extra: si WhatsApp no está instalado, "Copiar mensaje" y mostrar el número del bot.

### 10.2 Principal

`/principal` · `PrincipalScreen` · `usePrincipalScreen` · datos: `usePerfil`, `usePlanillasDeHoy`

- `EncabezadoNegocio`: `Avatar monogram` (iniciales en aro dorado) + **nombre del negocio** (`display`) + "Hola,
  {administrador}" + fecha de hoy ("Martes 24 de noviembre"). Ícono de Ayuda a la derecha.
- `GoogleStatusBanner` si el servidor no está conectado con Google (hoy el bot responde "el servidor aún no está
  autenticado con Google" en cada comando; aquí se avisa antes).
- **`TarjetaHoy`** (lo más usado cada día):
  - Con planilla de hoy: overline "PLANILLA DE HOY", "24-11-2026 · 2 hojas", `KpiGrid` (Ventas B40, Gastos B38,
    Saldo B58 de la última hoja) y botón "Continuar en Hoja 2" → Edición.
  - Sin planilla de hoy: "Aún no has creado la planilla de hoy" + botón "Crear la de hoy" (un toque, sin pasar por
    el formulario) + enlace "Elegir otra fecha" → Nueva planilla.
- `AccionesPrincipales` (grilla 2 columnas de `ActionTile`): **Crear planilla** (`featured`), **Crear planilla
  secundaria**, **Ver planillas**, **Ver trabajadores**, **Mi perfil**.
- Estados: skeleton de la tarjeta mientras carga; si `hoy` falla, la tarjeta muestra `ErrorState` compacto y la grilla
  sigue funcionando.
- Pull-to-refresh.

"Crear planilla secundaria" abre Nueva planilla con `fecha=hoy` y `hoja=siguiente` (la siguiente a la última que
existe hoy). Si hoy no hay primera, la pantalla lo explica y ofrece crear la primera.

### 10.3 Planillas

`/planillas` · `PlanillasScreen` · `usePlanillasScreen` · datos: `useMesesPlanillas`, `usePlanillasDelMes`

- `PistaDobleToque` (Banner `dorado-50`, se cierra y no vuelve): "Toca una planilla para registrar movimientos. Toca
  dos veces para abrirla en Google Sheets."
- `ListaMeses`: un `Accordion` por carpeta `mes-aaaa`, de la más reciente a la más antigua, título "Noviembre 2026" y
  subtítulo "12 planillas" (cuando ya se cargó). **El mes actual abierto por defecto.**
- Dentro de cada mes (carga perezosa al abrir): `FilaPlanillaInteractiva` por planilla, días de mayor a menor y,
  dentro del mismo día, Hoja 1, 2, 3. Cada fila: "Lun 24 nov" + `HojaBadge` + chevron.
- Gestos de la fila:
  - **Un toque** → Edición.
  - **Doble toque** → abre en Google Sheets (`utils/linking/googleSheets.ts`).
  - **Mantener presionado** → `AccionesPlanillaSheet`: Registrar movimientos · Ver resumen · Abrir en Google Sheets ·
    Copiar enlace. (Alternativa accesible al doble toque, que no se descubre solo.)
- FAB "+" → Nueva planilla.
- Estados: skeleton por mes; mes vacío ("No hay planillas en este mes"); negocio sin planillas (EmptyState con
  "Crear la primera").
- Pull-to-refresh recarga los meses y los meses abiertos.

### 10.4 Nueva planilla

`/planillas/nueva` · `NuevaPlanillaScreen` · `useNuevaPlanillaScreen` + `useFechaHojaSincronizadas`

- `SelectorFechaHoja` (una fila):
  - `DateField` "Fecha" (dd-mm-aaaa, por defecto hoy o `?fecha=`).
  - `Dropdown` "Hoja": **Primera** (por defecto), Segunda, Tercera. Si ya existe la tercera, aparece Cuarta, y así
    (siempre hasta "existentes + 1", mínimo tres).
- `CalendarioPlanillas` debajo:
  - Muestra el mes de la fecha escrita y la marca seleccionada (relleno esmeralda).
  - Tocar un día **cambia el texto** del campo; escribir una fecha válida **mueve el calendario**.
  - "Hoy" con aro dorado; puntos dorados debajo de los días que ya tienen planillas (uno por hoja, máximo 3).
- Disponibilidad de hojas para la fecha (`utils/planillas/disponibilidadHojas.ts`, con las planillas del mes):
  - Hoja que ya existe → la opción dice "Segunda · ya existe" y el botón cambia a **"Abrir planilla"**.
  - Hoja que todavía no se puede crear (falta la anterior) → deshabilitada con "Crea primero la primera".
- `AvisoSaldoInicial`: "El saldo de caja se tomará del saldo total de 23-11-2026 · Hoja 2", o, si no existe planilla
  del día anterior, Banner de aviso "No hay planilla del 23-11-2026: el saldo de caja empezará en 0" (lo mismo que
  hace el bot).
- Fecha futura → confirmación "Vas a crear una planilla con fecha futura".
- Botón inferior fijo: **"Crear planilla"** / **"Abrir planilla"** → `useCrearPlanilla` → `router.replace` a Edición.
  Los avisos del backend (`avisos`) se muestran como primer mensaje del chat.
- Errores: fecha inválida (bajo el campo); 422 del backend (Banner con el mensaje del bot).

### 10.5 Edición de planilla (chat)

`/planillas/[planillaId]` · `EdicionPlanillaScreen` · `useEdicionPlanillaScreen` + `useComposer` — detalle en §12.

- Encabezado: `TituloPlanilla` ("24-11-2026 · Hoja 2", subtítulo del negocio) + `AccionesEncabezado` (Resumen, Abrir
  en Google Sheets).
- Fondo `ledger` (renglones de libro contable al 3 %, como el fondo de WhatsApp).
- `ListaMensajes`: burbujas al estilo WhatsApp. Propias a la derecha (`esmeralda-100`, con "Gasto:" en
  `esmeralda-800` negrita); del bot a la izquierda, con **ícono y fondo según el tipo**: éxito `neutro-50` con
  check esmeralda, aviso `aviso-50` con triángulo ámbar, error `error-50` con ícono rojo (el ícono hace que no
  dependa solo del color). Hora y estado de envío (enviando / listo / falló → "Reintentar"). Separadores de día.
  El historial sale del SQLite del teléfono (§7.1).
- `IndicadorProcesando` mientras el bot responde.
- `OpcionesSeleccion` cuando el bot pregunta (varios trabajadores): opciones como chips tocables, más "Cancelar
  préstamo".
- `Composer` (solo visible con un comando elegido) + `BandaComandos` (siempre visible, una línea, desplazable).
- Extras: mantener presionada una burbuja → copiar; los enlaces del bot (resumen, nómina) se abren en Sheets;
  `ChatVacio` con "Elige un comando abajo para registrar el primer movimiento"; `GoogleStatusBanner`.

### 10.6 Resumen de planilla (nueva, recomendada)

`/planillas/[planillaId]/resumen` · `ResumenPlanillaScreen` · datos: `useResumenPlanilla`

- `TotalesPlanilla` (`KpiGrid`): Gastos del día (B38), Efectivo (B39), Venta total (B40), Saldo previo (B42), **Saldo
  total** (B58, destacado).
- `UsoSecciones`: una `ProgressBar` por sección con "12 de 24 filas": Compras, Préstamos, Administrador, Retiros,
  Inversiones, Aseo, Alimentación. Al llegar al 100 % muestra "Llena: crea una segunda planilla" con botón directo.
  (Hoy el usuario solo se entera cuando el bot rechaza un movimiento.)
- Acciones: Abrir en Google Sheets · Corregir saldos desde aquí (confirmación).
- Pull-to-refresh.

### 10.7 Trabajadores

`/trabajadores` · `TrabajadoresScreen` · datos: `useTrabajadores`

- `SearchField` (filtra en el teléfono ignorando tildes y mayúsculas, igual que el bot).
- `ListaTrabajadores`: `FilaTrabajador` con avatar de iniciales + nombre + chevron, orden alfabético con
  `SectionHeader` por letra. Contador "23 trabajadores".
- Estados: negocio sin carpeta de trabajadores (EmptyState: "Este negocio no tiene carpeta de trabajadores. Pídesela
  al proveedor del bot."); sin trabajadores ("Se crean solos al registrar el primer préstamo"); búsqueda sin
  resultados.

### 10.8 Detalle de trabajador

`/trabajadores/[trabajadorId]` · `DetalleTrabajadorScreen` · datos: `useTrabajador`

- `EncabezadoTrabajador`: avatar con aro dorado + nombre.
- `PeriodoActual` (Card): overline "PERÍODO ACTUAL", total de préstamos (B30, `amountLarge`), "9 de 16 vales usados"
  con `ProgressBar` (al llenarse: "Haz la nómina para cerrar el período").
- `ListaVales`: `ValeRow` (fecha + monto), del más reciente al más antiguo.
- `ListaNominas`: nóminas archivadas (títulos de las hojas: "24-11-2026", "24-11-2026 (2)") → Detalle nómina.
- `AccionesTrabajador`:
  - **Registrar préstamo** → Edición de la última planilla de hoy con `comando=trabajador&texto=<nombre>`. Si hoy no
    hay planilla, ofrece crearla primero.
  - **Pagar nómina** → igual con `comando=nomina`.
  - **Abrir en Google Sheets**.

### 10.9 Detalle de nómina (nueva, recomendada)

`/trabajadores/[trabajadorId]/nominas/[nominaId]` · `DetalleNominaScreen` · datos: `useNominaArchivada`

- Título con la fecha de la nómina, total de préstamos de ese período y lista de `ValeRow`. Botón "Abrir en Google
  Sheets" (abre el archivo en esa hoja si la plataforma lo permite).

### 10.10 Mi perfil

`/perfil` · `PerfilScreen` · datos: `usePerfil`

- `TarjetaNegocio`: nombre (editar → `/perfil/negocio`), estado, botones "Carpeta de planillas" y "Carpeta de
  trabajadores" (abren Drive).
- `TarjetaAdministrador`: nombre (editar → `/perfil/administrador`), identificador de WhatsApp (solo lectura, con nota
  "es tu identidad en el bot; para cambiarlo contacta al proveedor").
- `ListaAdministradores`: los demás administradores del negocio (solo lectura).
- Versión de la app y botón **Cerrar sesión** (`danger`, con confirmación).

### 10.11 Editar negocio / Editar administrador (nuevas, por usar stack)

`/perfil/negocio` y `/perfil/administrador` · formularios con `FormField` + `TextField` + botón "Guardar".

- Negocio: nombre (obligatorio, 2–80 caracteres). Nota: "Se usará en las planillas nuevas; las existentes no
  cambian."
- Administrador: nombre (obligatorio). Misma nota (va en B6 de las planillas nuevas).
- Al guardar: invalida `perfil`, toast "Guardado" y vuelve atrás.

### 10.12 Ayuda (nueva)

`/ayuda` · `AyudaScreen` · datos: `useComandos`

- Una `TarjetaComando` por comando: ícono, nombre, para qué sirve, ejemplo ("Gasto: 5.000 pan"), alias que también
  entiende WhatsApp.
- Sección "Cómo funciona": saldo que pasa de un día al siguiente, planillas adicionales en orden, deshacer, menús de
  trabajadores, límites por sección.

### 10.13 No encontrada

`+not-found` · `NoEncontradaScreen`: EmptyState + "Volver al inicio".

### 10.14 Resumen de pantallas sugeridas además de las tuyas

| Pantalla | Por qué |
|---|---|
| Vincular | Sin ella no hay forma de entrar (no existe login de administradores) |
| Resumen de planilla | Totales y **cuánto queda en cada sección** antes de que el bot rechace un movimiento |
| Detalle de nómina | Ver un período cerrado sin salir de la app |
| Editar negocio / Editar administrador | Con navegación stack, editar en su propia pantalla es más claro que en línea |
| Ayuda | Reemplaza `instrucciones`; sirve para administradores nuevos |
| (Fase 7) Dispositivos vinculados | Ver y revocar sesiones de la app |

---

## 11. Flujos

### 11.1 Primer uso

```
Abrir app ─▶ splash (restaurando) ─▶ sin refresh ─▶ Vincular
  ─▶ "Abrir WhatsApp" ─▶ enviar "VINCULAR 482913" ─▶ volver a la app
  ─▶ sondeo detecta "confirmada" ─▶ Principal
```

### 11.2 Día normal

```
Principal ─▶ TarjetaHoy "Crear la de hoy" ─▶ (POST /app/planillas {hoy, 1}) ─▶ Edición
  ─▶ toca "Efectivo" ─▶ teclado ─▶ "350.000" ─▶ Enviar ─▶ "Efectivo registrado: $350.000"
  ─▶ toca "Gasto" ─▶ "5.000 pan" ─▶ Enviar ─▶ (el comando sigue elegido) "3.000 leche" ─▶ Enviar
  ─▶ toca fuera ─▶ se oculta el teclado
  ─▶ ícono Resumen ─▶ Resumen (saldo total, secciones)
```

### 11.3 Sección llena

```
Edición: "Aseo: 2.000" ─▶ bot: aviso "La sección 'aseo' está llena (8 filas)…"
  ─▶ la burbuja de aviso incluye botón "Crear segunda planilla"
  ─▶ Nueva planilla (fecha de la planilla, hoja siguiente) ─▶ replace ─▶ Edición de la Hoja 2
```

### 11.4 Préstamo con nombre ambiguo

```
Edición: "Préstamo: 20.000 jose" ─▶ bot pregunta (seleccion) ─▶ banda deshabilitada
  ─▶ OpcionesSeleccion: [jose salon] [jose panadero] [+ Crear "jose"] [Cancelar préstamo]
  ─▶ toca "jose salon" ─▶ POST /seleccion {opcion: 1} ─▶ "📄 Préstamo guardado en el archivo de 'jose salon'"
  (Cancelar ─▶ DELETE /seleccion ─▶ "se canceló 'trabajador 20000 jose' y se borró de la planilla")
```

### 11.5 Deshacer

```
toca "Deshacer" ─▶ confirmar: "¿Deshacer gasto 5000 pan, gasto 3000 leche?" (texto de estado.deshacer)
  ─▶ Sí ─▶ "✅ Se deshizo: …"
  (si estado.deshacer es null ─▶ chip deshabilitado con "No hay nada que deshacer")
```

### 11.6 Planillas y doble toque

```
Planillas ─▶ (noviembre abierto) ─▶ toque en "Lun 24 nov · Hoja 2" ─▶ Edición
                                 └▶ doble toque ─▶ Google Sheets (app) / navegador si no está instalada
                                 └▶ mantener ─▶ hoja de acciones
```

### 11.7 Desde un trabajador

```
Trabajadores ─▶ buscar "mari" ─▶ María José ─▶ Detalle (9/16 vales)
  ─▶ "Registrar préstamo" ─▶ ¿hay planilla hoy?
        sí ─▶ Edición (última hoja de hoy) con "Préstamo:" y "maria jose" ya escrito; falta el monto
        no ─▶ "Primero crea la planilla de hoy" ─▶ Nueva planilla ─▶ …
```

### 11.8 Sesión vencida o revocada

```
cualquier petición ─▶ 401 ─▶ refresh ─▶ 401 ─▶ sinSesion ─▶ Vincular + alerta "Tu sesión terminó"
```

---

## 12. Edición de planilla en detalle

### 12.1 Distribución vertical

```
┌───────────────────────────────┐
│ ← 24-11-2026 · Hoja 2   📋 ⧉ │  AppHeader + filete dorado
├───────────────────────────────┤
│                               │
│   (mensajes, FlatList         │  DismissKeyboardArea: tocar aquí oculta el teclado
│    invertida, fondo ledger)   │
│                               │
├───────────────────────────────┤
│ Gasto: 5.000 pan|        [➤] │  Composer (solo con comando elegido)
├───────────────────────────────┤
│ [Libre][Gasto][Efectivo][Sal… │  BandaComandos: SIEMPRE visible, una línea, scroll horizontal
├───────────────────────────────┤
│           TECLADO             │  solo cuando se está escribiendo
└───────────────────────────────┘
```

Composer y banda van juntos al pie de un `KeyboardAvoider` (`KeyboardAvoidingView` de React Native,
`behavior="padding"` en las dos plataformas): la banda queda siempre justo encima del teclado y, sin teclado, encima
del área segura inferior. **Sin `keyboardVerticalOffset`:** con el encabezado de JS (`AppHeader`), el encabezado y la
pantalla son hermanos en un contenedor que empieza arriba de la ventana. La posición de la pantalla ya incluye el
encabezado; sumarlo otra vez dejaba un hueco de su alto (~110 dp en Android) entre la banda y el teclado.

La lista es una `FlatList` `inverted`. En Android eso es `scale: -1`, que también cambia izquierda por derecha, así
que el padding horizontal va en cada fila (`styles.row`) y no en el contenedor. Si no, las burbujas del bot quedan
pegadas al margen dorado.

### 12.2 Estados del composer (`composer.reducer.ts`)

| Estado | Banda | Composer | Teclado |
|---|---|---|---|
| `lectura` (sin comando) | visible | oculto | oculto |
| `escribiendo` (comando + foco) | visible, chip activo | visible | visible |
| `pausado` (comando + tocó fuera) | visible, chip activo | visible con el borrador | oculto |
| `enviando` | visible | deshabilitado | igual que antes |
| `esperandoSeleccion` | deshabilitada | oculto | oculto; se ven las opciones |

Eventos y reglas:

- **Elegir un comando con argumentos** → `escribiendo` (foco en el campo, abre teclado, haptic). El prefijo
  "Gasto:" aparece al inicio del campo en `esmeralda-700` negrita y **no se puede borrar como texto**: es un elemento
  aparte (`PrefijoComando`) a la izquierda del `TextInput`, así nunca se mezcla con lo que escribe el usuario.
- **Elegir otro comando** con borrador → cambia el prefijo y conserva el texto.
- **Tocar el comando activo** → lo deselecciona (`lectura`) y descarta el borrador.
- **Borrar con el campo vacío** → deselecciona (como quitar una mención en WhatsApp).
- **Tocar fuera** (lista de mensajes) → `Keyboard.dismiss()` → `pausado`. Tocar el composer → `escribiendo`.
- **Comandos sin argumentos**: Resumen se envía al instante; Deshacer y Corregir saldos piden confirmación.
- **Chip "Libre"** (primero de la banda): composer sin prefijo para lenguaje natural ("gasto 5000 pan y 3000
  leche"). Pasa por DeepSeek.
- **Préstamo / Nómina** → `SugerenciasTrabajador` encima del composer con nombres que coinciden (de `useTrabajadores`,
  normalizados). Tocar uno lo inserta. Reduce los menús de "varios trabajadores parecidos".
- **Enviar** → burbuja optimista con `client_id` (UUID), `enviando`, `IndicadorProcesando`. El comando **sigue
  elegido** y el teclado abierto para registrar varios seguidos (decisión abierta §15).
- **Error de red** → burbuja "No se envió · Reintentar" (mismo `client_id`: el backend no duplica).
- **Llega `seleccion`** → `esperandoSeleccion`: opciones en `OpcionesSeleccion`, banda deshabilitada con la nota "Si
  sales sin elegir, se cancelará 'trabajador 20000 jose'".
- **Abrir la pantalla con `?comando=&texto=`** → arranca en `escribiendo` con ese comando y texto.

### 12.3 Lista de mensajes

- `FlatList` invertida, `keyboardDismissMode="on-drag"`, `keyboardShouldPersistTaps="handled"`.
- Historial del SQLite local, paginado hacia atrás (50 por página, `id < último`) con `onEndReached`.
- Al entrar se pide `GET /app/planillas/{id}/estado`, que restaura la pregunta pendiente si la había y dice qué
  revertiría "Deshacer".
- Burbujas: texto seleccionable al mantener presionado (copiar); URL de Google Sheets → botón "Abrir planilla".

---

## 13. Pruebas

### 13.1 Backend (pytest, con los fakes de `tests/fakes.py`)

`FakeDrive` necesita carpetas de mes y padres para probar listados y pertenencia.

| Archivo | Casos |
|---|---|
| `tests/test_mobile_units.py` ✅ | Parser estricto (monto al inicio/final, "5.000", "$1.200.000", "5 mil" → DeepSeek); tipo de cada respuesta del bot; tokens (vencido, mal firmado, de otro secreto); todo comando del catálogo existe en el dispatcher; límite por IP; caché con vencimiento |
| `tests/test_mobile_api.py` ✅ | Vinculación (entrega única, código errado o vencido, número no registrado); refresh rota y el viejo deja de servir; logout y "cerrar app" cortan el acceso al instante; administrador desactivado → 401; sin token → 401; API apagada sin secreto → 503; perfil y nombres; catálogo con alias; crear hojas en orden y listar meses/mes; crear planilla no cancela la pregunta del chat; tarjeta de hoy; uso de secciones; planilla y trabajador de otro negocio → 404; Google desconectado → 503; lectura directa sin DeepSeek; respaldo a DeepSeek y chip "Libre"; `client_id` repetido no duplica; `hoja` desde el chat se rechaza; pregunta como botones, responder y cancelar; **canal separado** de WhatsApp; dos administradores en la misma planilla; trabajadores y nómina archivada; WhatsApp responde `VINCULAR` sin DeepSeek ni contabilidad |
| `tests/e2e/test_e2e_app.py` ✅ | 13 pruebas contra el bot local con Google y DeepSeek reales: vinculación por el webhook, sesiones, planillas, chat con y sin DeepSeek, reintento, canales separados, pregunta de trabajadores, nómina archivada, pertenencia, nombres y **lecturas concurrentes** (14 a la vez, tres rondas; antes tumbaban el bot) (detalle en `tests/e2e/README.md`) |
| `tests/test_units.py` ✅ | Además: cada hilo usa su propia conexión con Google (`google_api.thread_http`) y `execute` la usa |

### 13.2 App (jest-expo + Testing Library)

Implementado (19 suites, 65 pruebas, todas colocadas junto al archivo que prueban):

- `utils/`: fechas (máscara, validación, aritmética de días y meses, matriz del calendario, fecha relativa), montos,
  normalización, iniciales, limpieza de nombres, disponibilidad de hojas y sugerencias de trabajador.
- `composer.reducer.test.ts`: transiciones de §12.2.
- `api/mappers/mappers.test.ts`: DTO → entidad.
- `api/client/http.test.ts`: varios 401 simultáneos → un solo refresh; refresh rechazado → sesión vencida.
- Componentes: `Calendar` (texto ⇄ día), `Dropdown` (opciones deshabilitadas), `BandaComandos` + `Composer` (prefijo),
  `TapArea` (simple vs doble), `TextoConComando` (sin texto no lleva dos puntos).
- Antes de cerrar cada fase: `npx tsc --noEmit`, `npx expo lint` y `npx jest`.

---

## 14. Fases de implementación

| Fase | Alcance | Listo cuando |
|---|---|---|
| **0. Preparación de la app** ✅ | Borrar la plantilla de tabs; alias `@/*`; dependencias; `theme/`; fuentes; ESLint con reglas de capas; providers; navegación con pantallas vacías | Hecho |
| **1. Backend completo** ✅ | Todo §2: tablas, settings, tokens, vinculación por WhatsApp, canal en `SessionManager`, perfil, comandos, planillas, chat y trabajadores | Hecho (148 pruebas y 47 E2E). Falta configurar el servidor |
| **2. App: sesión** ✅ | `api/client`, `session/`, Vincular, restauración, refresco, Principal (encabezado + grilla), Perfil de solo lectura | Hecho: vinculación por el webhook de WhatsApp (simulado en local) y restauración al reabrir, vistas en el emulador |
| **3. Planillas** ✅ | App: Planillas (acordeón, gestos, hoja de acciones), Nueva planilla (calendario, selector de hoja), TarjetaHoy | Hecho en Android. Falta ver el doble toque en iOS |
| **4. Edición (chat)** ✅ | App: `src/storage/` (historial local, §7.1) y chat completo de §12 | Hecho: gasto, "Libre", préstamo con sugerencia, deshacer y reintento vistos en el emulador |
| **5. Trabajadores** ✅ | App: 3 pantallas + "Registrar préstamo / Pagar nómina" | Hecho: lista y detalle con datos reales de Sheets |
| **6. Pulido y entrega** (parcial) | Resumen, Ayuda, edición de perfil, estados vacíos/errores/skeletons, accesibilidad (lectores de pantalla, tamaño de letra), haptics, ícono y splash, `eas.json`, builds | Hecho, salvo ícono y splash definitivos, `eas.json` y builds de preview. La accesibilidad está en el código (etiquetas, roles y estados), pero falta probarla con TalkBack/VoiceOver y letra grande |
| **7. Futuro** | Notas de voz (Whisper ya existe en el backend), dispositivos vinculados, cambio de número con re-vinculación, avisos push ("otro administrador registró…"), cola sin conexión | — |

---

## 15. Riesgos y decisiones abiertas

| Tema | Recomendación | Alternativa |
|---|---|---|
| ¿El comando sigue elegido después de enviar? | ✅ **Decidido: sí** ("modo ráfaga") | — |
| Historial del chat | ✅ **Decidido: solo en el SQLite del teléfono** (§7.1). No se comparte entre administradores y se pierde al reinstalar | — |
| Hojas en el selector | ✅ **Decidido:** Primera, Segunda, Tercera y aparece la siguiente si ya existen todas | — |
| Teléfono del administrador | ✅ **Decidido:** solo lectura en v1 | Cambio con re-vinculación (fase 7) |
| Web | ✅ **Decidido (2026-11-26):** versión web para iPhone, pensada para el teléfono; escritorio después | — |
| Expo Go | ✅ **Resuelto:** sin gesture-handler ni keyboard-controller, toda la app corre en Expo Go (`expo-intent-launcher`, `expo-sqlite` y `expo-secure-store` vienen incluidos). La development build solo hará falta si se agrega una librería nativa | — |
| Cuota de Google | Lecturas perezosas, caché corta en backend y en React Query, nada de leer totales por trabajador en la lista | Pedir aumento de cuota |
| Latencia del chat | Parser estricto sin DeepSeek para lo que ya viene bien escrito | Siempre DeepSeek (más lento y con costo) |
| Toque simple con retraso | Inevitable al soportar doble toque (~250 ms). Se compensa con feedback visual inmediato al presionar | Usar solo "mantener presionado" para Sheets |

---

## 16. Pendiente de verificar en Expo SDK 58

`AGENTS.md` pide leer la documentación de la versión exacta antes de escribir código
(`https://docs.expo.dev/versions/v58.0.0/`). Resultado:

- ✅ `Stack.Protected`: acepta `redirectTo`; con eso no hace falta `app/index.tsx` de entrada.
- ✅ `react-native-keyboard-controller`: no viene en Expo Go; se usó `KeyboardAvoidingView` (ver §12.1).
- ✅ `react-native-gesture-handler`: no se usó; `TapArea` con `Pressable` y temporizador.
- ✅ `expo-secure-store`: Expo no pone límite, pero "algunas versiones de iOS rechazaban valores de más de ~2048
  bytes" y `setItemAsync` rechaza la promesa. El perfil crece con la lista de administradores, así que va en
  `expo-sqlite/kv-store` (no es secreto). En el llavero queda solo el refresh token.
- ✅ `expo-intent-launcher`: el doble toque abre `com.google.android.apps.docs.editors.sheets` en el emulador.
- ⏳ iOS: esquema `googlesheets://` declarado en `ios.infoPlist.LSApplicationQueriesSchemes`, con respaldo a
  `https://docs.google.com/...`. **Falta probarlo en un iPhone real.**
- ✅ `typedRoutes`: `routes.ts` tipa las rutas con grupos y parámetros (`tsc` limpio).
