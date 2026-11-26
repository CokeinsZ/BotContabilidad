// Cada peso desde su subcarpeta: importar el índice del paquete incluiría
// en la app TODOS los pesos de la familia (decenas de archivos .ttf).
import { Inter_400Regular } from '@expo-google-fonts/inter/400Regular';
import { Inter_500Medium } from '@expo-google-fonts/inter/500Medium';
import { Inter_600SemiBold } from '@expo-google-fonts/inter/600SemiBold';
import { Inter_700Bold } from '@expo-google-fonts/inter/700Bold';
import { PlayfairDisplay_600SemiBold } from '@expo-google-fonts/playfair-display/600SemiBold';

/** Archivos de fuente que carga `useFonts` al arrancar (ver providers/SplashGate). */
export const fontAssets = {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
  Inter_700Bold,
  PlayfairDisplay_600SemiBold,
};

/**
 * Familias por peso. En Android una fuente propia no debe combinarse con
 * `fontWeight`: cada peso es su propia familia.
 */
export const fonts = {
  regular: 'Inter_400Regular',
  medium: 'Inter_500Medium',
  semibold: 'Inter_600SemiBold',
  bold: 'Inter_700Bold',
  display: 'PlayfairDisplay_600SemiBold',
} as const;
