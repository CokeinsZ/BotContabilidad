import { Linking } from 'react-native';

/** Abre una URL (WhatsApp, Drive…). Devuelve false si el teléfono no pudo abrirla. */
export async function abrirUrl(url: string): Promise<boolean> {
  try {
    await Linking.openURL(url);
    return true;
  } catch {
    return false;
  }
}
