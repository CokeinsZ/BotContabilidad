import { Info } from 'lucide-react-native';

import { colors, sizes, type IconSize } from '@/theme';

import { iconRegistry, isIconName, type IconName } from './iconRegistry';

export interface IconProps {
  /** Nombre del registro. Un nombre desconocido (p. ej. un ícono nuevo del bot) muestra "info". */
  name: IconName | (string & {});
  size?: IconSize | number;
  color?: string;
  strokeWidth?: number;
}

/** Íconos de trazo uniforme. Son decorativos: el texto de al lado dice qué son. */
export function Icon({ name, size = 'md', color = colors.text.primary, strokeWidth = sizes.iconStroke }: IconProps) {
  const Component = isIconName(name) ? iconRegistry[name] : Info;
  const pixels = typeof size === 'number' ? size : sizes.icon[size];
  return <Component size={pixels} color={color} strokeWidth={strokeWidth} />;
}
