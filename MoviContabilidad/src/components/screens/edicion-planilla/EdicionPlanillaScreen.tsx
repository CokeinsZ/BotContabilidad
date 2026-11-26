import { Stack } from 'expo-router';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { GoogleStatusBanner } from '@/components/domain/estado';
import { HeaderActions } from '@/components/navigation';
import { ScreenBackground } from '@/components/ui/backgrounds';
import { DismissKeyboardArea, KeyboardAvoider, useKeyboardVisible } from '@/components/ui/keyboard';
import { useEdicionPlanillaScreen } from '@/hooks/screens/edicion-planilla/useEdicionPlanillaScreen';
import { spacing } from '@/theme';
import { tituloPlanilla } from '@/utils/planillas/ordinales';

import { BandaComandos } from './banda';
import { ChatVacio, ListaMensajes, OpcionesSeleccion } from './chat';
import { Composer } from './composer';
import { styles } from './EdicionPlanillaScreen.styles';
import { TituloPlanilla } from './encabezado/TituloPlanilla';
import { SugerenciasTrabajador } from './sugerencias';

export default function EdicionPlanillaScreen() {
  const s = useEdicionPlanillaScreen();
  const insets = useSafeAreaInsets();
  const tecladoVisible = useKeyboardVisible();
  const { composer, historial } = s;
  const titulo = s.planilla ? tituloPlanilla(s.planilla.fecha, s.planilla.hoja) : 'Planilla';
  const vacio = !historial.isLoading && historial.mensajes.length === 0 && !s.procesando;

  return (
    <>
      <Stack.Screen
        options={{
          headerTitle: () => <TituloPlanilla titulo={titulo} subtitulo={s.negocio} />,
          headerRight: () => (
            <HeaderActions
              actions={[
                { icon: 'resumen', label: 'Resumen de la planilla', onPress: s.verResumen },
                { icon: 'externo', label: 'Abrir en Google Sheets', onPress: s.abrirEnSheets },
              ]}
            />
          ),
        }}
      />
      <KeyboardAvoider>
        <ScreenBackground variant="ledger">
          {!s.googleConectado ? (
            <View style={styles.banner}>
              <GoogleStatusBanner conectado={false} />
            </View>
          ) : null}
          <DismissKeyboardArea>
            {vacio ? (
              <ChatVacio />
            ) : (
              <ListaMensajes
                mensajes={historial.mensajes}
                hoy={s.hoy}
                etiquetas={s.etiquetas}
                procesando={s.procesando}
                hayMas={!!historial.hasNextPage}
                onCargarMas={() => void historial.fetchNextPage()}
                onReintentar={s.reintentar}
                onCopiar={s.copiar}
                onAbrirEnlace={s.abrirEnlace}
                onCrearSegunda={s.crearSegundaPlanilla}
              />
            )}
          </DismissKeyboardArea>
          <View style={[styles.footer, { paddingBottom: tecladoVisible ? 0 : insets.bottom }]}>
            {s.seleccion ? (
              <OpcionesSeleccion
                seleccion={s.seleccion}
                ocupado={s.procesando}
                onElegir={s.elegirOpcion}
                onCancelar={s.cancelarPregunta}
              />
            ) : null}
            {composer.activo && !s.seleccion ? (
              <>
                <SugerenciasTrabajador trabajadores={s.sugerencias} onElegir={composer.completarTrabajador} />
                <Composer
                  inputRef={composer.inputRef}
                  etiqueta={composer.etiqueta}
                  texto={composer.texto}
                  placeholder={composer.placeholder}
                  puedeEnviar={composer.puedeEnviar && !s.procesando}
                  onTexto={composer.cambiarTexto}
                  onBorrarVacio={composer.borrarVacio}
                  onEnviar={s.enviarComposer}
                />
              </>
            ) : null}
            <BandaComandos
              comandos={s.comandos}
              seleccionado={composer.comandoId}
              deshabilitada={!!s.seleccion}
              deshacerDisponible={s.deshacerDisponible}
              onElegir={s.elegirComando}
            />
            {tecladoVisible ? null : <View style={{ height: spacing.xs }} />}
          </View>
        </ScreenBackground>
      </KeyboardAvoider>
    </>
  );
}
