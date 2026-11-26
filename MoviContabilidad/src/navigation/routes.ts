/**
 * Rutas de la app. Los componentes nunca escriben rutas a mano: usan esto.
 * `hoja: 'siguiente'` = la hoja que sigue a la última que existe ese día.
 */
import type { Href } from 'expo-router';

export const routes = {
  principal: '/' as const,
  vincular: '/vincular' as const,
  planillas: '/planillas' as const,
  trabajadores: '/trabajadores' as const,
  perfil: '/perfil' as const,
  editarNegocio: '/perfil/negocio' as const,
  editarAdministrador: '/perfil/administrador' as const,
  ayuda: '/ayuda' as const,

  nuevaPlanilla: (params: { fecha?: string; hoja?: number | 'siguiente' } = {}): Href => ({
    pathname: '/planillas/nueva',
    params: {
      ...(params.fecha ? { fecha: params.fecha } : {}),
      ...(params.hoja !== undefined ? { hoja: String(params.hoja) } : {}),
    },
  }),

  planilla: (planillaId: string, params: { comando?: string; texto?: string } = {}): Href => ({
    pathname: '/planillas/[planillaId]',
    params: { planillaId, ...params },
  }),

  resumenPlanilla: (planillaId: string): Href => ({
    pathname: '/planillas/[planillaId]/resumen',
    params: { planillaId },
  }),

  trabajador: (trabajadorId: string): Href => ({
    pathname: '/trabajadores/[trabajadorId]',
    params: { trabajadorId },
  }),

  nomina: (trabajadorId: string, nominaId: number): Href => ({
    pathname: '/trabajadores/[trabajadorId]/nominas/[nominaId]',
    params: { trabajadorId, nominaId: String(nominaId) },
  }),
};
