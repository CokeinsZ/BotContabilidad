import { View } from 'react-native';

import { ActionTile } from '@/components/ui/buttons';

import { styles } from './PrincipalScreen.styles';

interface AccionesPrincipalesProps {
  subtituloSecundaria: string;
  onCrearPlanilla: () => void;
  onPlanillaSecundaria: () => void;
  onPlanillas: () => void;
  onTrabajadores: () => void;
  onPerfil: () => void;
}

export function AccionesPrincipales(props: AccionesPrincipalesProps) {
  return (
    <View style={styles.tiles}>
      <View style={styles.tileRow}>
        <ActionTile icon="crearPlanilla" title="Crear planilla" subtitle="Elegir fecha y hoja" variant="featured" onPress={props.onCrearPlanilla} />
        <ActionTile icon="planillaSecundaria" title="Planilla secundaria" subtitle={props.subtituloSecundaria} onPress={props.onPlanillaSecundaria} />
      </View>
      <View style={styles.tileRow}>
        <ActionTile icon="carpeta" title="Ver planillas" subtitle="Por mes, como en Drive" onPress={props.onPlanillas} />
        <ActionTile icon="trabajadores" title="Trabajadores" subtitle="Préstamos y nóminas" onPress={props.onTrabajadores} />
      </View>
      <ActionTile icon="perfil" title="Mi perfil" subtitle="Negocio y administrador" wide onPress={props.onPerfil} />
    </View>
  );
}
