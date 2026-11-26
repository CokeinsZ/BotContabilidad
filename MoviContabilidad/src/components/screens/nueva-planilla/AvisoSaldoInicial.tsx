import type { PlanillaBasica } from '@/utils/planillas/disponibilidadHojas';
import { Banner } from '@/components/ui/feedback';

interface AvisoSaldoInicialProps {
  hoja: number;
  existe: boolean;
  fechaAnterior: string | null;
  origen: PlanillaBasica | null;
  cargando: boolean;
}

/** De dónde sale el saldo de caja (B42), con las mismas reglas del bot. */
export function AvisoSaldoInicial({ hoja, existe, fechaAnterior, origen, cargando }: AvisoSaldoInicialProps) {
  if (cargando || existe) return null;
  if (origen) {
    return (
      <Banner
        tone="info"
        icon="saldo"
        message={`El saldo de caja inicial se tomará del saldo total de ${origen.fecha} · Hoja ${origen.hoja}.`}
      />
    );
  }
  if (hoja === 1 && fechaAnterior) {
    return (
      <Banner
        tone="warning"
        message={`No hay planilla del ${fechaAnterior}: el saldo de caja de esta planilla empezará en 0.`}
      />
    );
  }
  return null;
}
