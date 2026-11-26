/** Escala de 4 pt. Nunca se usan números sueltos para márgenes o separaciones. */
export const spacing = {
  none: 0,
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
  /** Margen lateral de las pantallas. */
  gutter: 20,
} as const;

export type SpacingToken = keyof typeof spacing;
