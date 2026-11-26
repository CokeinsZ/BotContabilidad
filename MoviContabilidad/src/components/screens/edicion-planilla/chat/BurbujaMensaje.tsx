import { Pressable, View } from 'react-native';

import type { Mensaje, TipoMensaje } from '@/api/entities';
import { Button } from '@/components/ui/buttons';
import { Icon, type IconName } from '@/components/ui/icons';
import { Text } from '@/components/ui/typography';
import { colors, toneColors, type Tone } from '@/theme';
import { horaCorta } from '@/utils/dates/fechaRelativa';

import { styles } from './Chat.styles';
import { TextoConComando } from './TextoConComando';
import { TextoConEnlaces } from './TextoConEnlaces';

const TIPO: Record<Exclude<TipoMensaje, 'enviado'>, { icon: IconName; tone: Tone }> = {
  exito: { icon: 'exito', tone: 'success' },
  aviso: { icon: 'aviso', tone: 'warning' },
  error: { icon: 'error', tone: 'danger' },
  info: { icon: 'info', tone: 'info' },
  seleccion: { icon: 'trabajadores', tone: 'gold' },
};

interface BurbujaMensajeProps {
  mensaje: Mensaje;
  etiquetaComando: string | null;
  onReintentar: (mensaje: Mensaje) => void;
  onCopiar: (texto: string) => void;
  onAbrirEnlace: (url: string) => void;
  onCrearSegunda: () => void;
}

export function BurbujaMensaje({ mensaje, etiquetaComando, onReintentar, onCopiar, onAbrirEnlace, onCrearSegunda }: BurbujaMensajeProps) {
  if (mensaje.autor === 'yo') {
    return (
      <View>
        <Pressable
          onLongPress={() => onCopiar(mensaje.texto)}
          accessibilityRole="text"
          accessibilityLabel={`Tú: ${etiquetaComando ? `${etiquetaComando}, ` : ''}${mensaje.texto}`}
          style={[styles.bubble, styles.own]}
        >
          <TextoConComando etiqueta={etiquetaComando} texto={mensaje.texto} />
          <View style={styles.meta}>
            <Text variant="micro">{horaCorta(mensaje.creadoEn)}</Text>
            {mensaje.estadoEnvio === 'enviando' ? <Icon name="reloj" size={12} color={colors.text.secondary} /> : null}
            {mensaje.estadoEnvio === 'enviado' ? <Icon name="checkDoble" size={13} color={colors.action.primary} /> : null}
            {mensaje.estadoEnvio === 'fallido' ? <Icon name="error" size={13} color={colors.text.danger} /> : null}
          </View>
        </Pressable>
        {mensaje.estadoEnvio === 'fallido' ? (
          <Pressable style={styles.retry} onPress={() => onReintentar(mensaje)} accessibilityRole="button" accessibilityLabel="Reintentar envío">
            <Text variant="captionStrong" tone="danger">
              No se envió · Reintentar
            </Text>
          </Pressable>
        ) : null}
      </View>
    );
  }

  const tipo = mensaje.tipo === 'enviado' ? TIPO.info : TIPO[mensaje.tipo];
  const tono = toneColors(tipo.tone);
  const sugiereSegunda = mensaje.tipo === 'aviso' && mensaje.texto.toLowerCase().includes('segunda planilla');
  return (
    <Pressable
      onLongPress={() => onCopiar(mensaje.texto)}
      accessibilityRole="text"
      style={[styles.bubble, styles.bot, mensaje.tipo === 'aviso' || mensaje.tipo === 'error' ? { backgroundColor: tono.bg, borderColor: tono.border } : null]}
    >
      <View style={styles.botIcon}>
        <Icon name={tipo.icon} size="sm" color={tono.icon} />
      </View>
      <View style={styles.botBody}>
        <TextoConEnlaces texto={mensaje.texto} onAbrirEnlace={onAbrirEnlace} />
        {sugiereSegunda ? <Button label="Crear segunda planilla" size="sm" variant="secondary" onPress={onCrearSegunda} /> : null}
        <View style={styles.meta}>
          <Text variant="micro">{horaCorta(mensaje.creadoEn)}</Text>
        </View>
      </View>
    </Pressable>
  );
}
