import { useQueryClient } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';

import { useAlert, useToast } from '@/components/ui/feedback';
import { usePerfil } from '@/hooks/data/perfil/usePerfil';
import { queryKeys } from '@/hooks/data/queryKeys';
import { routes } from '@/navigation/routes';
import { useSession } from '@/session';
import { borrarHistorial } from '@/storage';
import { abrirUrl } from '@/utils/linking/externos';

export function usePerfilScreen() {
  const router = useRouter();
  const alert = useAlert();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { cerrarSesion, administradorId } = useSession();
  const perfil = usePerfil();

  const abrirCarpeta = async (url: string | null) => {
    if (url && !(await abrirUrl(url))) toast.show('No se pudo abrir Google Drive.', 'danger');
  };

  return {
    perfil,
    version: Constants.expoConfig?.version ?? '—',
    editarNegocio: () => router.push(routes.editarNegocio),
    editarAdministrador: () => router.push(routes.editarAdministrador),
    abrirCarpetaPlanillas: () => void abrirCarpeta(perfil.data?.negocio.carpetaPlanillasUrl ?? null),
    abrirCarpetaTrabajadores: () => void abrirCarpeta(perfil.data?.negocio.carpetaTrabajadoresUrl ?? null),
    borrarHistorial: async () => {
      if (administradorId === null) return;
      const ok = await alert.confirmar({
        titulo: 'Borrar el historial del chat',
        mensaje: 'Se borran los mensajes guardados en este teléfono. Lo registrado en las planillas no cambia.',
        textoConfirmar: 'Borrar',
        destructiva: true,
      });
      if (!ok) return;
      await borrarHistorial(administradorId);
      await queryClient.invalidateQueries({ queryKey: queryKeys.chat.todoElHistorial });
      toast.show('Historial borrado');
    },
    cerrarSesion: async () => {
      const ok = await alert.confirmar({
        titulo: 'Cerrar sesión',
        mensaje: 'Para volver a entrar tendrás que vincular la app otra vez desde tu WhatsApp.',
        textoConfirmar: 'Cerrar sesión',
        destructiva: true,
      });
      if (ok) await cerrarSesion();
    },
  };
}
