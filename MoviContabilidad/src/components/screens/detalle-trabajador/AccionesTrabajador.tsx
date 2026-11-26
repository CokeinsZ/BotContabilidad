import { Column } from '@/components/ui/layout';
import { Button } from '@/components/ui/buttons';

interface AccionesTrabajadorProps {
  onPrestar: () => void;
  onPagarNomina: () => void;
  onAbrirEnSheets: () => void;
}

export function AccionesTrabajador({ onPrestar, onPagarNomina, onAbrirEnSheets }: AccionesTrabajadorProps) {
  return (
    <Column gap="sm">
      <Button label="Registrar préstamo" icon="prestamo" fullWidth onPress={onPrestar} />
      <Button label="Pagar nómina" icon="nomina" variant="secondary" fullWidth onPress={onPagarNomina} />
      <Button label="Abrir en Google Sheets" icon="externo" variant="ghost" fullWidth onPress={onAbrirEnSheets} />
    </Column>
  );
}
