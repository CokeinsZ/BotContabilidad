# MoviContabilidad

App móvil (Expo SDK 58) del bot de contabilidad: registra en las planillas de Google Sheets lo mismo que se hace por
WhatsApp, desde el teléfono. El plan, las decisiones y el estado están en
[docs/plan-app-movil.md](docs/plan-app-movil.md).

## Correr la app

```bash
npm install
cp .env.example .env     # EXPO_PUBLIC_API_URL: a qué bot se conecta
npx expo start           # abre en Expo Go (Android o iOS)
```

Todo corre en Expo Go: no hace falta una development build. `EXPO_PUBLIC_API_URL` se lee al empaquetar; después de
cambiarla, reinicia `npx expo start`.

### Contra el bot local

1. En la raíz del repositorio: `docker compose -f docker-compose.local.yml up -d --build`.
2. En `.env`:
   - Emulador de Android: `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`
   - Simulador de iOS: `EXPO_PUBLIC_API_URL=http://localhost:8000`
   - Teléfono físico: el compose local solo escucha en `127.0.0.1`, así que el teléfono no llega al bot local. Usa
     el servidor.
3. Vincular: la app muestra un código de 6 dígitos. Envíalo como el administrador de pruebas (999), en la raíz del
   repositorio:

   ```bash
   uv run python dev/send.py "VINCULAR 123456"
   ```

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
  `api/client/transport.ts`). `storage/` guarda el historial del chat en SQLite, solo en el teléfono. El resto son
  `session/`, `navigation/`, `components/` (`ui`, `domain`, `navigation`, `screens`), `hooks/`, `theme/` y `utils/`.
  El detalle está en §4 del plan.
