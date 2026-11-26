import * as Haptics from 'expo-haptics';

/** Vibración corta al elegir un comando o enviar. Si el teléfono no la soporta, no pasa nada. */
export function vibrarSeleccion(): void {
  Haptics.selectionAsync().catch(() => undefined);
}

export function vibrarEnvio(): void {
  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => undefined);
}
