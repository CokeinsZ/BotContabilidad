export const sizes = {
  /** Área táctil mínima (accesibilidad). */
  touchTarget: 44,
  control: { sm: 36, md: 44, lg: 52 },
  icon: { sm: 16, md: 20, lg: 24, xl: 28 },
  iconStroke: 1.75,
  avatar: { sm: 32, md: 44, lg: 64 },
  hairline: 1,
  /** Ancho máximo de una burbuja del chat respecto al ancho de la pantalla. */
  bubbleMaxWidth: '84%',
} as const;

export type IconSize = keyof typeof sizes.icon;
