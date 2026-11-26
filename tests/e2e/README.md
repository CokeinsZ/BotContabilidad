# Pruebas E2E

Prueban el bot **de punta a punta**: cada prueba escribe al webhook real de
WhatsApp del bot local, el mensaje pasa por **DeepSeek real**, el bot escribe
en **Google Sheets/Drive reales**, y la prueba verifica leyendo Google
directamente (valores, tipos de dato, fórmulas, hojas y archivos).

## Cómo correrlas

```bash
docker compose -f docker-compose.local.yml up -d --build   # bot + Evolution simulada
uv run pytest --e2e -v                 # todas (varios minutos)
uv run pytest --e2e -v -s              # mostrando la conversación con el bot
uv run pytest --e2e -k trabajadores    # solo un grupo
E2E_KEEP=1 uv run pytest --e2e ...     # conserva la carpeta de Drive para revisarla
```

Sin `--e2e`, `uv run pytest` solo corre las pruebas unitarias (y omite estas).

Requisitos (en el `.env`):

- `E2E_DRIVE_FOLDER_ID`: carpeta de Drive donde cada corrida crea su
  subcarpeta `E2E <fecha-hora>`.
- `AUTH_ADMIN_PASSWORD`: para la prueba de `/auth`.
- `APP_JWT_SECRET`: para las pruebas de la app (`test_e2e_app.py`). El compose
  local sube el límite de códigos de vinculación por IP (`APP_PAIRINGS_PER_IP`).

## Aislamiento

Cada corrida:

1. Crea en Drive `E2E <fecha-hora>/` con `planillas/` y `trabajadores/`.
2. Registra en la base local (`bot_contabilidad.db`, la misma que monta el
   contenedor) un negocio de prueba con esas carpetas y otro **sin** carpeta
   de trabajadores.
3. Cada prueba usa un administrador nuevo (teléfono aleatorio): sesión
   limpia, sin planilla activa ni deshacer.
4. Al terminar borra los negocios de la base y manda la carpeta a la
   papelera (salvo `E2E_KEEP=1`).

Cada prueba usa sus propias fechas y nombres de trabajador para no
interferir con las demás. `corregir_saldos` recorre todas las planillas del
negocio, así que su prueba usa un negocio propio.

## Qué cubren

| Archivo | Casos |
|---|---|
| `test_e2e_limites.py` | Llenar TODAS las secciones (gastos 24, administrador 9, retiros 21, inversiones 6, aseo 8, alimentación 5) y rechazar el excedente sin pisar encabezados, fórmulas ni totales; deshacer libera espacio; sección llena + deshacer de otro admin (compactación). |
| `test_e2e_planillas.py` | `corregir_saldos` (negocio propio: encadena días, adicionales, cambio de mes y huecos; deshacer; lenguaje natural); segunda, tercera y cuarta planilla; saldo total (B58) → saldo efectivo (B42) como número, incluso negativo; el día siguiente toma la planilla más alta; orden obligatorio; seleccionar sin duplicar; fecha explícita; cambio de mes y de año; saldo anterior no numérico; el saldo se copia al crear; resumen igual a la planilla. |
| `test_e2e_trabajadores.py` | Mismo nombre con distinto apellido/descripción (jose salon / jose panadero); nombres que se contienen (jose / josefina); menú, opción inválida, crear desde el menú; menú sin responder cancela el préstamo / la nómina / el retiro y lo borra de la planilla; dos préstamos ambiguos en un mensaje (un menú a la vez); mayúsculas, tildes y ñ; nómina, deshacer de nómina, dos nóminas el mismo día, nómina vía retiro; nómina ambigua (sin opción de crear); deshacer de nómina con vales nuevos de otro admin; límite de 16 vales; archivos sin plantilla o sin hoja "principal"; negocio sin carpeta de trabajadores. |
| `test_e2e_deshacer_y_concurrencia.py` | Deshacer un mensaje con todos los tipos de comando; deshacer dentro del mismo mensaje; un mensaje fallido no reemplaza el deshacer; un admin no deshace lo del otro; celda cambiada por otro admin; 4 admins llenando la misma sección a la vez. |
| `test_e2e_webhook.py` | El webhook responde en menos de 1 s y procesa en segundo plano; un mensaje reenviado (mismo id) se procesa una sola vez; la respuesta "1" a un menú enviada sin esperar se procesa en orden. |
| `test_e2e_general.py` | Número no registrado; mensaje sin comandos; sin planilla activa; instrucciones; lenguaje natural ("la hoja de hoy" + varios gastos con "5.000"); `/auth` protegido. |
| `test_e2e_app.py` | API de la app móvil (`/app`). La app se vincula enviando `VINCULAR <código>` por el webhook real: entrega única de la sesión, refresh que rota, logout y `cerrar app` cortan el acceso, código errado y número no registrado; crear hojas en orden, reabrir, listar meses y planillas (cada prueba con negocio propio); tarjeta de hoy con los totales de Sheets; chat sin DeepSeek ("pan 5.000") y con DeepSeek ("5 mil de pan", varios gastos en texto libre); reintento con el mismo `client_id` sin duplicar; "pon la hoja del…" no cambia de planilla; sesiones de app y WhatsApp separadas (cada `deshacer` revierte solo lo suyo); pregunta de trabajadores como opciones, responder y cancelar; detalle del trabajador y nómina archivada (vales en A4:C19, total en B21); otro negocio recibe 404; renombrar negocio y administrador se refleja en las planillas nuevas. |

## Notas

- DeepSeek es un modelo de lenguaje: las pruebas usan sobre todo comandos
  explícitos ("gasto 1001 insumo, ...") para ser deterministas. Si una
  prueba falla porque DeepSeek devolvió algo distinto, el mensaje del
  `assert` muestra la conversación completa (con `-s`).
- Google limita las escrituras a ~60 por minuto por usuario. El bot
  reintenta con espera, así que algunas pruebas tardan más de lo normal.
- El audio (Whisper) no se prueba aquí.
