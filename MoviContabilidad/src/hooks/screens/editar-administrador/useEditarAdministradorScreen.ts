import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { useActualizarPerfil } from '@/hooks/data/perfil/useActualizarPerfil';
import { useFormularioNombre } from '@/hooks/shared/useFormularioNombre';

export function useEditarAdministradorScreen() {
  const perfil = usePerfil();
  const actualizar = useActualizarPerfil('administrador');
  return useFormularioNombre(perfil.data?.administrador.nombre ?? '', actualizar.mutateAsync);
}
