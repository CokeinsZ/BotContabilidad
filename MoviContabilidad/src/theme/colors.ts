import { palette } from './palette';

/** Tokens semánticos: lo único que usan los componentes para pintar. */
export const colors = {
  background: {
    screen: palette.blanco,
    surface: palette.neutro50,
    sunken: palette.neutro100,
    overlay: 'rgba(18, 22, 20, 0.36)',
  },
  text: {
    primary: palette.tinta,
    strong: palette.neutro800,
    secondary: palette.neutro600,
    muted: palette.neutro400,
    inverse: palette.blanco,
    /** Texto secundario sobre fondos esmeralda. */
    inverseSoft: palette.esmeralda100,
    gold: palette.dorado700,
    action: palette.esmeralda700,
    danger: palette.error700,
    warning: palette.aviso700,
    success: palette.esmeralda800,
  },
  border: {
    subtle: palette.neutro100,
    default: palette.neutro200,
    focus: palette.esmeralda300,
    gold: palette.dorado500,
    danger: palette.error200,
  },
  action: {
    primary: palette.esmeralda700,
    primaryPressed: palette.esmeralda800,
    primarySoft: palette.esmeralda50,
    primarySoftPressed: palette.esmeralda100,
    focusRing: palette.esmeralda50,
  },
  decoration: {
    gold: palette.dorado500,
    goldLight: palette.dorado300,
    goldSoft: palette.dorado100,
    goldWash: palette.dorado50,
    goldIcon: palette.dorado600,
  },
  chat: {
    ownBubble: palette.esmeralda100,
    botBubble: palette.neutro50,
    commandPrefix: palette.esmeralda700,
    ownCommandPrefix: palette.esmeralda800,
    ledgerLine: 'rgba(18, 22, 20, 0.05)',
    ledgerMargin: 'rgba(201, 162, 39, 0.35)',
  },
  status: {
    success: { fg: palette.esmeralda800, bg: palette.esmeralda50, border: palette.esmeralda100, icon: palette.esmeralda700 },
    warning: { fg: palette.aviso700, bg: palette.aviso50, border: palette.aviso200, icon: palette.aviso700 },
    danger: { fg: palette.error700, bg: palette.error50, border: palette.error200, icon: palette.error700 },
    info: { fg: palette.neutro800, bg: palette.neutro50, border: palette.neutro200, icon: palette.neutro600 },
    gold: { fg: palette.dorado700, bg: palette.dorado50, border: palette.dorado100, icon: palette.dorado600 },
  },
} as const;

export type StatusTone = keyof typeof colors.status;
