import type { NativeStackNavigationOptions } from 'expo-router';

interface ScreenConfig {
  name: string;
  options: NativeStackNavigationOptions;
}

/** Pantallas del grupo (app) y su título. Los títulos dinámicos los pone cada pantalla. */
export const appScreens: ScreenConfig[] = [
  { name: 'index', options: { headerShown: false } },
  { name: 'planillas/index', options: { title: 'Planillas' } },
  { name: 'planillas/nueva', options: { title: 'Nueva planilla' } },
  { name: 'planillas/[planillaId]/index', options: { title: 'Planilla' } },
  { name: 'planillas/[planillaId]/resumen', options: { title: 'Resumen' } },
  { name: 'trabajadores/index', options: { title: 'Trabajadores' } },
  { name: 'trabajadores/[trabajadorId]/index', options: { title: 'Trabajador' } },
  { name: 'trabajadores/[trabajadorId]/nominas/[nominaId]', options: { title: 'Nómina' } },
  { name: 'perfil/index', options: { title: 'Mi perfil' } },
  { name: 'perfil/negocio', options: { title: 'Editar negocio' } },
  { name: 'perfil/administrador', options: { title: 'Editar administrador' } },
  { name: 'ayuda', options: { title: 'Ayuda' } },
];
