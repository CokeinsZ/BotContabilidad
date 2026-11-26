import { useEffect, useState } from 'react';
import { Animated, type DimensionValue } from 'react-native';

import { radii } from '@/theme';

import { styles } from './Feedback.styles';

export interface SkeletonProps {
  width?: DimensionValue;
  height: number;
  radius?: number;
}

/** Bloque gris que late mientras carga el contenido real. */
export function Skeleton({ width = '100%', height, radius = radii.sm }: SkeletonProps) {
  const [opacity] = useState(() => new Animated.Value(0.5));
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 650, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.5, duration: 650, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [opacity]);
  return <Animated.View style={[styles.skeleton, { width, height, borderRadius: radius, opacity }]} />;
}
