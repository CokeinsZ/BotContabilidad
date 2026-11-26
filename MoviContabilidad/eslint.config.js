// Reglas de capas de la app (ver docs/plan-app-movil.md §3.3).
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

const negocio = ['@/api', '@/api/*', '@/session', '@/session/*', '@/storage', '@/storage/*', '@/hooks/*'];

module.exports = defineConfig([
  expoConfig,
  { ignores: ['dist/*', '.expo/*', 'node_modules/*'] },
  {
    // 1. Solo el transporte HTTP puede usar fetch.
    files: ['src/**/*.{ts,tsx}', 'app/**/*.{ts,tsx}'],
    ignores: ['src/api/client/transport.ts'],
    rules: {
      'no-restricted-globals': [
        'error',
        { name: 'fetch', message: 'Solo src/api/client/transport.ts puede usar fetch: usa una función de src/api/endpoints.' },
      ],
    },
  },
  {
    // 2. components/ui es transversal: no sabe nada del negocio.
    files: ['src/components/ui/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            { group: [...negocio, '@/components/domain', '@/components/domain/*', '@/components/screens/*', '@/navigation', '@/navigation/*'], message: 'components/ui no puede depender del negocio ni de la navegación.' },
          ],
        },
      ],
    },
  },
  {
    // 3. components/domain solo usa tipos de api/entities (nada de datos ni sesión).
    files: ['src/components/domain/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            { group: ['@/api/client/*', '@/api/endpoints/*', '@/api/dto/*', '@/api/mappers/*', '@/session', '@/session/*', '@/storage', '@/storage/*', '@/hooks/*', '@/components/screens/*'], message: 'components/domain solo puede importar tipos de @/api/entities.' },
          ],
        },
      ],
    },
  },
  {
    // 4. app/ solo enruta: re-exporta pantallas y layouts.
    files: ['app/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            { group: [...negocio, '@/components/ui', '@/components/ui/*', '@/components/domain', '@/components/domain/*', '@/theme', '@/theme/*'], message: 'app/ solo enruta: re-exporta una pantalla de @/components/screens o usa @/navigation.' },
          ],
        },
      ],
    },
  },
]);
