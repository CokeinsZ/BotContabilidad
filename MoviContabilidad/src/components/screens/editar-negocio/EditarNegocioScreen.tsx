import { FormularioNombre } from '@/components/domain/perfil';
import { useEditarNegocioScreen } from '@/hooks/screens/editar-negocio/useEditarNegocioScreen';

export default function EditarNegocioScreen() {
  const formulario = useEditarNegocioScreen();
  return (
    <FormularioNombre
      {...formulario}
      etiqueta="Nombre del negocio"
      nota="Se escribe en el encabezado de las planillas nuevas. Las que ya existen no cambian."
    />
  );
}
