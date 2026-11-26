import { Banner } from '@/components/ui/feedback';

/** Se muestra hasta que el usuario la cierra (queda guardado en el teléfono). */
export function PistaDobleToque({ onCerrar }: { onCerrar: () => void }) {
  return (
    <Banner
      tone="gold"
      icon="tocar"
      message="Toca una planilla para registrar movimientos. Tócala dos veces para abrirla en Google Sheets. Mantenla presionada para más opciones."
      onDismiss={onCerrar}
    />
  );
}
