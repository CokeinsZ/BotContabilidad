import { View } from 'react-native';

import { Banner, ErrorState, Spinner } from '@/components/ui/feedback';
import { Text } from '@/components/ui/typography';
import type { FaseVinculacion } from '@/hooks/screens/vincular/useVincularScreen';

import { styles } from './VincularScreen.styles';

interface EstadoVinculacionProps {
  fase: FaseVinculacion;
  error: string | null;
  onGenerarOtro: () => void;
}

export function EstadoVinculacion({ fase, error, onGenerarOtro }: EstadoVinculacionProps) {
  if (fase === 'esperando') {
    return (
      <View style={styles.status} accessibilityLiveRegion="polite">
        <Spinner />
        <Text tone="secondary">Esperando que el bot confirme…</Text>
      </View>
    );
  }
  if (fase === 'vencida') {
    return (
      <Banner
        tone="warning"
        title="El código venció"
        message="Los códigos duran 5 minutos. Genera uno nuevo y envíalo por WhatsApp."
        action={{ label: 'Generar otro código', onPress: onGenerarOtro }}
      />
    );
  }
  if (fase === 'error') {
    return <ErrorState compact message={error ?? 'No se pudo pedir un código.'} onRetry={onGenerarOtro} />;
  }
  return null;
}
