import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { useActualizarPerfil } from '@/hooks/data/perfil/useActualizarPerfil';
import { useFormularioNombre } from '@/hooks/shared/useFormularioNombre';

export function useEditarNegocioScreen() {
  const perfil = usePerfil();
  const actualizar = useActualizarPerfil('negocio');
  return useFormularioNombre(perfil.data?.negocio.nombre ?? '', actualizar.mutateAsync);
}
