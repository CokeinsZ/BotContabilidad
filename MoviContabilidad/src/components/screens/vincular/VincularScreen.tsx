import { View } from 'react-native';

import { Button } from '@/components/ui/buttons';
import { GoldDivider } from '@/components/ui/decorations';
import { LoadingState } from '@/components/ui/feedback';
import { Screen } from '@/components/ui/layout';
import { Text } from '@/components/ui/typography';
import { useVincularScreen } from '@/hooks/screens/vincular/useVincularScreen';

import { CodigoVinculacion } from './CodigoVinculacion';
import { EstadoVinculacion } from './EstadoVinculacion';
import { PasosVinculacion } from './PasosVinculacion';
import { styles } from './VincularScreen.styles';

export default function VincularScreen() {
  const { fase, vinculacion, segundosRestantes, error, abrirWhatsApp, copiarMensaje, generarOtro } = useVincularScreen();
  const conCodigo = vinculacion !== null && (fase === 'esperando' || fase === 'vencida');
  return (
    <Screen scroll edges={['top', 'bottom']} background="hero" watermark="BC" contentStyle={styles.content}>
      <View style={styles.heading}>
        <Text variant="overline">Bot Contabilidad</Text>
        <Text variant="display" align="center" accessibilityRole="header">
          Conecta tu WhatsApp
        </Text>
        <Text tone="secondary" align="center" style={styles.subtitle}>
          La app sabrá cuál es tu negocio sin pedirte contraseña.
        </Text>
      </View>
      <GoldDivider variant="ornament" />
      {fase === 'creando' ? <LoadingState message="Pidiendo un código…" /> : null}
      {conCodigo ? (
        <>
          <CodigoVinculacion codigo={vinculacion.codigo} segundosRestantes={segundosRestantes} />
          <PasosVinculacion />
          {fase === 'esperando' ? (
            <View style={styles.buttons}>
              <Button label="Abrir WhatsApp" icon="whatsapp" size="lg" fullWidth onPress={abrirWhatsApp} />
              <Button label="Copiar mensaje" icon="copiar" variant="ghost" fullWidth onPress={copiarMensaje} />
            </View>
          ) : null}
        </>
      ) : null}
      <EstadoVinculacion fase={fase} error={error} onGenerarOtro={generarOtro} />
    </Screen>
  );
}
