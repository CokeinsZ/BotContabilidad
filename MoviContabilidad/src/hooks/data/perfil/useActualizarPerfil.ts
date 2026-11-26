import { useMutation } from '@tanstack/react-query';

import { actualizarAdministrador, actualizarNegocio } from '@/api';
import { useSession } from '@/session';

/** Cambia el nombre del negocio o del administrador y guarda el perfil que devuelve el bot. */
export function useActualizarPerfil(campo: 'negocio' | 'administrador') {
  const { recordarPerfil } = useSession();
  return useMutation({
    mutationFn: (nombre: string) => (campo === 'negocio' ? actualizarNegocio(nombre) : actualizarAdministrador(nombre)),
    onSuccess: (perfil) => recordarPerfil(perfil),
  });
}
