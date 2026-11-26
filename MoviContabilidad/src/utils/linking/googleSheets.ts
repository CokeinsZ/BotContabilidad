import { startActivityAsync } from 'expo-intent-launcher';
import { Linking, Platform } from 'react-native';

const SHEETS_ANDROID_PACKAGE = 'com.google.android.apps.docs.editors.sheets';

/**
 * Abre una planilla en la app Google Sheets; si no está instalada, en el navegador.
 *
 * - Android: intent VIEW dirigido al paquete de Sheets.
 * - iOS: esquema `googlesheets://` (declarado en app.json → LSApplicationQueriesSchemes).
 * - Si nada de eso funciona: la URL https (enlace universal o navegador).
 */
export async function abrirEnGoogleSheets(url: string): Promise<void> {
  if (Platform.OS === 'android') {
    try {
      await startActivityAsync('android.intent.action.VIEW', { data: url, packageName: SHEETS_ANDROID_PACKAGE });
      return;
    } catch {
      // Sheets no está instalada: se sigue con el navegador.
    }
  }
  if (Platform.OS === 'ios') {
    const appUrl = url.replace(/^https:\/\//, 'googlesheets://');
    try {
      if (await Linking.canOpenURL(appUrl)) {
        await Linking.openURL(appUrl);
        return;
      }
    } catch {
      // Se sigue con la URL https.
    }
  }
  await Linking.openURL(url);
}
