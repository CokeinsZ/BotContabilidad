import { Text } from '@/components/ui/typography';
import { colors } from '@/theme';

/** "Gasto: 5.000 pan" con el comando en esmeralda negrita; sin texto, solo "Deshacer". */
export function TextoConComando({ etiqueta, texto, propio = true }: { etiqueta: string | null; texto: string; propio?: boolean }) {
  const conTexto = texto.trim().length > 0;
  return (
    <Text selectable>
      {etiqueta ? (
        <Text variant="bodyStrong" style={{ color: propio ? colors.chat.ownCommandPrefix : colors.chat.commandPrefix }}>
          {conTexto ? `${etiqueta}: ` : etiqueta}
        </Text>
      ) : null}
      {texto}
    </Text>
  );
}
