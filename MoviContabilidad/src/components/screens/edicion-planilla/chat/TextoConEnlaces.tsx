import { Text } from '@/components/ui/typography';

import { styles } from './Chat.styles';

const URL_PARTS = /(https?:\/\/[^\s"]+)/;
const IS_URL = /^https?:\/\//;

/** Texto del bot: los enlaces de Google Sheets se pueden tocar. */
export function TextoConEnlaces({ texto, onAbrirEnlace }: { texto: string; onAbrirEnlace: (url: string) => void }) {
  const partes = texto.split(URL_PARTS);
  return (
    <Text selectable>
      {partes.map((parte, index) =>
        IS_URL.test(parte) ? (
          <Text key={index} tone="action" style={styles.link} onPress={() => onAbrirEnlace(parte)} accessibilityRole="link">
            Abrir en Google Sheets
          </Text>
        ) : (
          <Text key={index}>{parte}</Text>
        ),
      )}
    </Text>
  );
}
