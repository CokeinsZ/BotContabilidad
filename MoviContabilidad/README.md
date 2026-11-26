# MoviContabilidad

App del bot de contabilidad (Expo SDK 58): registra en las planillas de Google Sheets lo mismo que se hace por
WhatsApp, desde el teléfono. Se entrega de dos formas:

- **Android:** APK instalable (EAS Build).
- **iPhone:** versión web en Safari ("Agregar a pantalla de inicio" la deja como una app). No hay build de iOS: no se
  usa el Apple Developer Program.

El plan, las decisiones y el estado están en [docs/plan-app-movil.md](docs/plan-app-movil.md).

## Correr la app

```bash
npm install
cp .env.example .env     # EXPO_PUBLIC_API_URL: a qué bot se conecta
npx expo start           # abre en Expo Go (Android o iOS); w abre la web
```

Todo corre en Expo Go: no hace falta una development build. `EXPO_PUBLIC_API_URL` se lee al empaquetar; después de
cambiarla, reinicia `npx expo start`. El `.env` tiene prioridad sobre una variable del shell: para usar otra URL sin
tocarlo, antepón `EXPO_NO_DOTENV=1`.

### Contra el bot local

1. En la raíz del repositorio: `docker compose -f docker-compose.local.yml up -d --build`.
2. URL del bot:
   - Emulador de Android: `http://10.0.2.2:8000`
   - Simulador de iOS y web en el PC: `http://localhost:8000`
   - Teléfono físico: el compose local solo escucha en `127.0.0.1`, así que el teléfono no llega al bot local. Usa
     el servidor.
3. Web: usa el puerto **8082** (`npx expo start --web --port 8082`), porque el 8081 lo ocupa `evolution-mock`. El
   compose local también levanta la web ya construida en http://localhost:8083; el bot local acepta (CORS) los dos.
4. Vincular: la app muestra un código de 6 dígitos. Envíalo como el administrador de pruebas (999), en la raíz del
   repositorio:

   ```bash
   uv run python dev/send.py "VINCULAR 123456"
   ```

## APK de Android

```bash
npx eas-cli@latest build -p android --profile preview
```

Al terminar, EAS da un enlace para descargar el APK (también en expo.dev, en Builds). En el teléfono: abrir el
enlace, descargar e instalar (Android pide permitir "instalar apps desconocidas" la primera vez). El perfil `preview`
de `eas.json` ya trae `EXPO_PUBLIC_API_URL` del servidor (el `.env` no se sube a EAS) y sube el `versionCode` en
cada build, así que un APK nuevo se instala encima del anterior. La llave de firma la guarda EAS.

## Versión web (iPhone)

```bash
npx expo export -p web   # genera dist/ con la URL del .env
```

- En el servidor: el servicio `movicontabilidad-web` del `docker-compose.yml` de la raíz construye la imagen
  ([Dockerfile](Dockerfile)) y la sirve con nginx ([docker/nginx.conf](docker/nginx.conf): rutas de la app →
  `index.html`, caché larga para los archivos con hash). Cómo publicarla: README de la raíz, "Versión web de la app".
- `dist/` es una SPA: cualquier otro hosting debe responder `index.html` para cualquier ruta (p. ej. EAS Hosting:
  `npx eas-cli@latest deploy --prod`).
- El bot tiene que aceptar el dominio de la web: agrégalo a `APP_WEB_ORIGINS` en el `.env` del servidor (CORS) y
  reinicia el bot.
- En el iPhone: abrir la URL en Safari → Compartir → "Agregar a pantalla de inicio".

Diferencias con la app nativa: en la web el historial del chat, el perfil y el token de sesión se guardan en
`localStorage` del navegador (archivos `*.web.ts` de `src/storage/`); el doble toque en una planilla abre Google
Sheets en una pestaña. `public/index.html` es la plantilla HTML (viewport para el teléfono, manifiesto e íconos) y
`src/providers/VisualViewportRoot.web.tsx` mantiene la banda de comandos encima del teclado.

## Antes de dar algo por terminado

```bash
npm run typecheck   # tsc --noEmit
npm run lint        # ESLint, con las reglas de capas (§3.3 del plan)
npm test            # Jest
```

## Estructura

- `app/`: solo rutas. Cada archivo re-exporta una pantalla de `src/components/screens/`; los `_layout` no tienen
  lógica.
- `src/`: todo lo demás. `api/` es lo único que habla con el bot (y el único `fetch` está en
  `api/client/transport.ts`). `storage/` guarda el historial del chat solo en el dispositivo (SQLite en el teléfono,
  `localStorage` en la web). El resto son `session/`, `navigation/`, `components/` (`ui`, `domain`, `navigation`,
  `screens`), `hooks/`, `theme/` y `utils/`. El detalle está en §4 del plan.
- `public/`: archivos de la web que se copian tal cual (`index.html`, `manifest.json`, íconos).
- `icono.jpg`: el ícono original. Los PNG de `assets/images/` y `public/icons/` salen de él.
