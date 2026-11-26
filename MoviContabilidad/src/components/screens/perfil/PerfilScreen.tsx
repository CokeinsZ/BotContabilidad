import { errorMessage } from '@/api';
import { Button } from '@/components/ui/buttons';
import { GoogleStatusBanner } from '@/components/domain/estado';
import { ErrorState, LoadingState } from '@/components/ui/feedback';
import { Column, Screen } from '@/components/ui/layout';
import { Text } from '@/components/ui/typography';
import { usePerfilScreen } from '@/hooks/screens/perfil/usePerfilScreen';

import { ListaAdministradores } from './ListaAdministradores';
import { TarjetaAdministrador } from './TarjetaAdministrador';
import { TarjetaNegocio } from './TarjetaNegocio';

export default function PerfilScreen() {
  const s = usePerfilScreen();
  const { perfil } = s;
  if (perfil.isLoading && !perfil.data) return <LoadingState />;
  if (!perfil.data) {
    return <ErrorState message={perfil.error ? errorMessage(perfil.error) : 'Sin datos.'} onRetry={() => void perfil.refetch()} />;
  }
  const datos = perfil.data;
  return (
    <Screen scroll refreshing={perfil.isRefetching} onRefresh={() => void perfil.refetch()}>
      <GoogleStatusBanner conectado={datos.googleConectado} />
      <TarjetaNegocio
        negocio={datos.negocio}
        onEditar={s.editarNegocio}
        onCarpetaPlanillas={s.abrirCarpetaPlanillas}
        onCarpetaTrabajadores={s.abrirCarpetaTrabajadores}
      />
      <TarjetaAdministrador administrador={datos.administrador} onEditar={s.editarAdministrador} />
      <ListaAdministradores administradores={datos.administradores} />
      <Column gap="sm">
        <Button label="Borrar historial del chat de este teléfono" icon="borrar" variant="outline" fullWidth onPress={s.borrarHistorial} />
        <Button label="Cerrar sesión" icon="salir" variant="danger" fullWidth onPress={s.cerrarSesion} />
        <Text variant="micro" align="center">
          MoviContabilidad {s.version}
        </Text>
      </Column>
    </Screen>
  );
}
