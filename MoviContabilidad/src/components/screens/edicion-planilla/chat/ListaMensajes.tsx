import { useMemo } from 'react';
import { FlatList, View } from 'react-native';

import type { Mensaje } from '@/api/entities';
import { etiquetaDia } from '@/utils/dates/fechaRelativa';
import { formatFecha } from '@/utils/dates/fechaPlanilla';

import { BurbujaMensaje } from './BurbujaMensaje';
import { styles } from './Chat.styles';
import { IndicadorProcesando } from './IndicadorProcesando';
import { SeparadorDia } from './SeparadorDia';

type Elemento = { tipo: 'mensaje'; mensaje: Mensaje } | { tipo: 'dia'; clave: string; etiqueta: string };

interface ListaMensajesProps {
  /** Del más nuevo al más viejo. */
  mensajes: Mensaje[];
  hoy: string;
  etiquetas: Map<string, string>;
  procesando: boolean;
  hayMas: boolean;
  onCargarMas: () => void;
  onReintentar: (mensaje: Mensaje) => void;
  onCopiar: (texto: string) => void;
  onAbrirEnlace: (url: string) => void;
  onCrearSegunda: () => void;
}

/** Lista invertida (lo nuevo abajo, como WhatsApp) con un separador por día. */
export function ListaMensajes({ mensajes, hoy, etiquetas, procesando, hayMas, onCargarMas, ...acciones }: ListaMensajesProps) {
  const elementos = useMemo<Elemento[]>(() => {
    const result: Elemento[] = [];
    mensajes.forEach((mensaje, index) => {
      result.push({ tipo: 'mensaje', mensaje });
      const siguiente = mensajes[index + 1];
      const dia = formatFecha(new Date(mensaje.creadoEn));
      if (!siguiente || formatFecha(new Date(siguiente.creadoEn)) !== dia) {
        result.push({ tipo: 'dia', clave: `dia-${dia}-${mensaje.id}`, etiqueta: etiquetaDia(mensaje.creadoEn, hoy) });
      }
    });
    return result;
  }, [mensajes, hoy]);

  return (
    <FlatList
      inverted
      data={elementos}
      keyExtractor={(item) => (item.tipo === 'mensaje' ? `m-${item.mensaje.id}` : item.clave)}
      contentContainerStyle={styles.list}
      keyboardDismissMode="on-drag"
      keyboardShouldPersistTaps="handled"
      onEndReached={hayMas ? onCargarMas : undefined}
      onEndReachedThreshold={0.4}
      ListHeaderComponent={procesando ? <IndicadorProcesando /> : undefined}
      ListHeaderComponentStyle={styles.row}
      renderItem={({ item }) => (
        <View style={styles.row}>
          {item.tipo === 'dia' ? (
            <SeparadorDia etiqueta={item.etiqueta} />
          ) : (
            <BurbujaMensaje
              mensaje={item.mensaje}
              etiquetaComando={item.mensaje.comando ? (etiquetas.get(item.mensaje.comando) ?? item.mensaje.comando) : null}
              {...acciones}
            />
          )}
        </View>
      )}
    />
  );
}
