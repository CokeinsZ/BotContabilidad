/** Sombras muy suaves: sobre blanco puro separan mejor los bordes que las sombras. */
export const shadows = {
  none: {},
  floating: { boxShadow: '0px 8px 20px rgba(11, 110, 79, 0.28)' },
  sheet: { boxShadow: '0px -6px 24px rgba(18, 22, 20, 0.10)' },
  toast: { boxShadow: '0px 6px 18px rgba(18, 22, 20, 0.16)' },
} as const;
