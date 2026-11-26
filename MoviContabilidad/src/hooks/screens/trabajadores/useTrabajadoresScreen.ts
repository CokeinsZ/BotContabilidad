import { useRouter } from 'expo-router';
import { useMemo, useState } from 'react';

import type { Trabajador } from '@/api';
import { useTrabajadores } from '@/hooks/data/trabajadores/useTrabajadores';
import { routes } from '@/navigation/routes';
import { normalizar } from '@/utils/text/normalizar';

export interface SeccionTrabajadores {
  title: string;
  data: Trabajador[];
}

/** Lista con búsqueda (sin tildes ni mayúsculas, como el bot) y secciones por letra. */
export function useTrabajadoresScreen() {
  const router = useRouter();
  const query = useTrabajadores();
  const [busqueda, setBusqueda] = useState('');

  const secciones = useMemo<SeccionTrabajadores[]>(() => {
    const consulta = normalizar(busqueda);
    const porLetra = new Map<string, Trabajador[]>();
    for (const trabajador of query.data?.trabajadores ?? []) {
      if (consulta && !normalizar(trabajador.nombre).includes(consulta)) continue;
      const letra = normalizar(trabajador.nombre).charAt(0).toUpperCase() || '#';
      porLetra.set(letra, [...(porLetra.get(letra) ?? []), trabajador]);
    }
    return [...porLetra.entries()].map(([title, data]) => ({ title, data }));
  }, [busqueda, query.data]);

  const total = query.data?.trabajadores.length ?? 0;
  return {
    query,
    carpetaConfigurada: query.data?.carpetaConfigurada ?? true,
    busqueda,
    setBusqueda,
    secciones,
    total,
    encontrados: secciones.reduce((suma, seccion) => suma + seccion.data.length, 0),
    abrir: (trabajador: Trabajador) => router.push(routes.trabajador(trabajador.id)),
  };
}
