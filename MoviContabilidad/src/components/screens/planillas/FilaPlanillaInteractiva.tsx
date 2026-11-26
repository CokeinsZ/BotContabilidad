import type { Planilla } from '@/api/entities';
import { PlanillaRow } from '@/components/domain/planillas';
import { TapArea } from '@/components/ui/gestures';
import { APP } from '@/constants/app';
import { diaCorto } from '@/utils/dates/fechaRelativa';

interface FilaPlanillaInteractivaProps {
  planilla: Planilla;
  onAbrir: (planilla: Planilla) => void;
  onAbrirEnSheets: (planilla: Planilla) => void;
  onAcciones: (planilla: Planilla) => void;
}

/** Un toque: registrar movimientos. Doble toque: Google Sheets. Mantener: más acciones. */
export function FilaPlanillaInteractiva({ planilla, onAbrir, onAbrirEnSheets, onAcciones }: FilaPlanillaInteractivaProps) {
  return (
    <TapArea
      delayMs={APP.doubleTapDelayMs}
      onPress={() => onAbrir(planilla)}
      onDoubleTap={() => onAbrirEnSheets(planilla)}
      onLongPress={() => onAcciones(planilla)}
      accessibilityLabel={`${diaCorto(planilla.fecha)}, hoja ${planilla.hoja}`}
      accessibilityHint="Abre el chat de la planilla. Mantén presionado para más acciones."
    >
      {({ pressed }) => <PlanillaRow planilla={planilla} pressed={pressed} />}
    </TapArea>
  );
}
