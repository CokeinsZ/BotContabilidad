import type { Planilla } from '@/api/entities';
import { ActionSheet } from '@/components/ui/overlays';
import { diaCorto } from '@/utils/dates/fechaRelativa';

interface AccionesPlanillaSheetProps {
  planilla: Planilla | null;
  onCerrar: () => void;
  onAbrir: (planilla: Planilla) => void;
  onResumen: (planilla: Planilla) => void;
  onAbrirEnSheets: (planilla: Planilla) => void;
  onCopiarEnlace: (planilla: Planilla) => void;
}

/** Lo mismo que los gestos, accesible y visible (el doble toque no se descubre solo). */
export function AccionesPlanillaSheet({ planilla, onCerrar, onAbrir, onResumen, onAbrirEnSheets, onCopiarEnlace }: AccionesPlanillaSheetProps) {
  return (
    <ActionSheet
      visible={planilla !== null}
      onClose={onCerrar}
      title={planilla ? `${diaCorto(planilla.fecha)} · Hoja ${planilla.hoja}` : undefined}
      actions={
        planilla
          ? [
              { id: 'abrir', label: 'Registrar movimientos', icon: 'libre', onPress: () => onAbrir(planilla) },
              { id: 'resumen', label: 'Ver resumen', icon: 'resumen', onPress: () => onResumen(planilla) },
              { id: 'sheets', label: 'Abrir en Google Sheets', icon: 'externo', onPress: () => onAbrirEnSheets(planilla) },
              { id: 'copiar', label: 'Copiar enlace', icon: 'copiar', onPress: () => onCopiarEnlace(planilla) },
            ]
          : []
      }
    />
  );
}
