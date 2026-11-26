/** Claves de React Query. Toda invalidación usa estas funciones, nunca arreglos sueltos. */
export const queryKeys = {
  perfil: ['perfil'] as const,
  comandos: ['comandos'] as const,
  vinculacion: (id: string) => ['vinculacion', id] as const,
  planillas: {
    all: ['planillas'] as const,
    meses: ['planillas', 'meses'] as const,
    mesesYMeses: ['planillas', 'mes'] as const,
    delMes: (anio: number, mes: number) => ['planillas', 'mes', anio, mes] as const,
    hoy: ['planillas', 'hoy'] as const,
    detalle: (id: string) => ['planillas', 'detalle', id] as const,
    resumen: (id: string) => ['planillas', 'resumen', id] as const,
  },
  chat: {
    estado: (planillaId: string) => ['chat', 'estado', planillaId] as const,
    historial: (administradorId: number, planillaId: string) => ['chat', 'historial', administradorId, planillaId] as const,
    todoElHistorial: ['chat', 'historial'] as const,
  },
  trabajadores: {
    all: ['trabajadores'] as const,
    lista: ['trabajadores', 'lista'] as const,
    detalle: (id: string) => ['trabajadores', 'detalle', id] as const,
    nomina: (id: string, hojaId: number) => ['trabajadores', 'nomina', id, hojaId] as const,
  },
} as const;
