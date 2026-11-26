/**
 * Paleta cruda de la app (ver docs/plan-app-movil.md §8.3).
 *
 * Los componentes NO importan este archivo: usan los tokens semánticos de
 * `colors.ts`. Así un modo oscuro futuro solo agrega otro `colors.ts`.
 */
export const palette = {
  blanco: '#FFFFFF',

  neutro50: '#F6F7F6',
  neutro100: '#ECEEEC',
  neutro200: '#DDE1DE',
  neutro400: '#8B928E',
  neutro600: '#5F6661',
  neutro800: '#2C312E',
  tinta: '#121614',

  esmeralda50: '#EEF8F3',
  esmeralda100: '#D3EFE2',
  esmeralda300: '#7CC9A6',
  esmeralda500: '#1F9D6E',
  esmeralda700: '#0B6E4F',
  esmeralda800: '#085A41',
  esmeralda900: '#063F2E',

  dorado50: '#FBF6E8',
  dorado100: '#F4E7C3',
  dorado300: '#E3C677',
  dorado500: '#C9A227',
  dorado600: '#A8841A',
  dorado700: '#8A6A10',

  error50: '#FEF3F2',
  error200: '#FECDCA',
  error700: '#B42318',

  aviso50: '#FFFAEB',
  aviso200: '#F6D9A8',
  aviso700: '#B54708',

  teclado: '#ADB3BA',
} as const;
