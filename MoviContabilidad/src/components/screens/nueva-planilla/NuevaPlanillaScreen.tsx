import { Button } from '@/components/ui/buttons';
import { Banner } from '@/components/ui/feedback';
import { Screen } from '@/components/ui/layout';
import { useNuevaPlanillaScreen } from '@/hooks/screens/nueva-planilla/useNuevaPlanillaScreen';

import { AvisoSaldoInicial } from './AvisoSaldoInicial';
import { CalendarioPlanillas } from './CalendarioPlanillas';
import { SelectorFechaHoja } from './SelectorFechaHoja';

export default function NuevaPlanillaScreen() {
  const s = useNuevaPlanillaScreen();
  return (
    <Screen
      scroll
      footer={
        <Button
          label={s.accion === 'abrir' ? 'Abrir planilla' : 'Crear planilla'}
          icon={s.accion === 'abrir' ? 'hoja' : 'crearPlanilla'}
          size="lg"
          fullWidth
          loading={s.enviando}
          disabled={!s.puedeEnviar}
          onPress={s.enviar}
        />
      }
    >
      <SelectorFechaHoja
        texto={s.texto}
        onTexto={s.cambiarFecha}
        errorFecha={s.errorFecha}
        opciones={s.opciones}
        hoja={s.hoja}
        onHoja={s.setHoja}
      />
      <CalendarioPlanillas
        mes={s.mesVisible}
        onMes={s.setMesVisible}
        seleccionado={s.fecha}
        onSeleccionar={s.cambiarFecha}
        hoy={s.hoy}
        marcas={s.marcas}
      />
      {s.errorHojas ? <Banner tone="danger" message={s.errorHojas} /> : null}
      <AvisoSaldoInicial
        hoja={s.hoja}
        existe={!!s.seleccion?.existe}
        fechaAnterior={s.fechaAnterior}
        origen={s.origen}
        cargando={s.cargandoHojas}
      />
    </Screen>
  );
}
