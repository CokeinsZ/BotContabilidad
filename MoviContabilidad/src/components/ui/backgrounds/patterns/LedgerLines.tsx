import { StyleSheet, View } from 'react-native';
import Svg, { Defs, Line, Pattern, Rect } from 'react-native-svg';

import { colors } from '@/theme';

const ROW = 26;
const MARGIN_X = 20;

/** Renglones de libro contable al 5 % y un margen dorado (fondo del chat, como el de WhatsApp). */
export function LedgerLines() {
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <Svg width="100%" height="100%">
        <Defs>
          <Pattern id="renglones" width={ROW} height={ROW} patternUnits="userSpaceOnUse">
            <Line x1={0} y1={ROW - 0.5} x2={ROW} y2={ROW - 0.5} stroke={colors.chat.ledgerLine} strokeWidth={1} />
          </Pattern>
        </Defs>
        <Rect x={0} y={0} width="100%" height="100%" fill="url(#renglones)" />
        <Line x1={MARGIN_X} y1={0} x2={MARGIN_X} y2="100%" stroke={colors.chat.ledgerMargin} strokeWidth={1} />
      </Svg>
    </View>
  );
}
