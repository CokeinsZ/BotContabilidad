import { StyleSheet } from 'react-native';

import { colors, radii, sizes, spacing } from '@/theme';

export const styles = StyleSheet.create({
  // El padding horizontal no va en el contenedor: en Android la lista invertida
  // usa scale(-1) y cambiaría izquierda por derecha. Cada fila lleva el suyo
  // (dentro de la celda la orientación vuelve a ser la normal).
  list: { paddingVertical: spacing.md, gap: spacing.sm },
  /** A la derecha del margen dorado del fondo (LedgerLines, x = 20). */
  row: { paddingLeft: spacing['2xl'], paddingRight: spacing.md },
  bubble: { maxWidth: sizes.bubbleMaxWidth, paddingHorizontal: spacing.md, paddingTop: spacing.sm, paddingBottom: spacing.xs, borderRadius: radii.bubble },
  own: { alignSelf: 'flex-end', backgroundColor: colors.chat.ownBubble, borderBottomRightRadius: radii.bubbleTail },
  bot: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    gap: spacing.sm,
    backgroundColor: colors.chat.botBubble,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    borderBottomLeftRadius: radii.bubbleTail,
  },
  botBody: { flexShrink: 1, gap: spacing.xs },
  botIcon: { paddingTop: 2 },
  meta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: spacing.xxs, marginTop: spacing.xxs },
  retry: { alignSelf: 'flex-end', flexDirection: 'row', alignItems: 'center', gap: spacing.xs, paddingVertical: spacing.xs },
  separator: {
    alignSelf: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xxs,
    marginVertical: spacing.xs,
    borderRadius: radii.pill,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.screen,
  },
  processing: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.bubble,
    backgroundColor: colors.chat.botBubble,
  },
  link: { textDecorationLine: 'underline' },
  option: {
    minHeight: sizes.touchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.md,
    borderWidth: sizes.hairline,
    borderColor: colors.border.default,
    backgroundColor: colors.background.screen,
  },
  optionPressed: { backgroundColor: colors.action.primarySoft },
  optionNumber: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.action.primarySoft,
  },
});
