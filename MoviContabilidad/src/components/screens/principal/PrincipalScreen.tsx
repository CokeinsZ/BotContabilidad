import { errorMessage } from '@/api';
import { GoogleStatusBanner } from '@/components/domain/estado';
import { GoldDivider } from '@/components/ui/decorations';
import { Screen } from '@/components/ui/layout';
import { usePrincipalScreen } from '@/hooks/screens/principal/usePrincipalScreen';
import { iniciales } from '@/utils/text/iniciales';

import { AccionesPrincipales } from './AccionesPrincipales';
import { EncabezadoNegocio } from './EncabezadoNegocio';
import { TarjetaHoy } from './TarjetaHoy';

export default function PrincipalScreen() {
  const s = usePrincipalScreen();
  const negocio = s.perfil?.negocio.nombre ?? 'Mi negocio';
  return (
    <Screen
      scroll
      edges={['top', 'bottom']}
      background="hero"
      watermark={iniciales(negocio)}
      refreshing={s.refrescando}
      onRefresh={s.refrescar}
    >
      <EncabezadoNegocio
        negocio={negocio}
        administrador={s.perfil?.administrador.nombre ?? ''}
        fechaHoy={s.fechaHoy}
        onAyuda={s.irA.ayuda}
      />
      <GoldDivider />
      {s.perfil ? <GoogleStatusBanner conectado={s.perfil.googleConectado} /> : null}
      <TarjetaHoy
        hoy={s.hoy.data}
        cargando={s.hoy.isLoading}
        error={s.hoy.error ? errorMessage(s.hoy.error) : null}
        creando={s.creando}
        onContinuar={s.continuar}
        onCrearLaDeHoy={s.crearLaDeHoy}
        onElegirFecha={s.irA.crearPlanilla}
        onReintentar={() => void s.hoy.refetch()}
      />
      <AccionesPrincipales
        subtituloSecundaria={s.subtituloSecundaria}
        onCrearPlanilla={s.irA.crearPlanilla}
        onPlanillaSecundaria={s.irA.planillaSecundaria}
        onPlanillas={s.irA.planillas}
        onTrabajadores={s.irA.trabajadores}
        onPerfil={s.irA.perfil}
      />
    </Screen>
  );
}
