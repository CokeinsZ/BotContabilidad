import { FormularioNombre } from '@/components/domain/perfil';
import { useEditarAdministradorScreen } from '@/hooks/screens/editar-administrador/useEditarAdministradorScreen';

export default function EditarAdministradorScreen() {
  const formulario = useEditarAdministradorScreen();
  return (
    <FormularioNombre
      {...formulario}
      etiqueta="Tu nombre"
      nota="Se escribe como administrador en las planillas nuevas. Las que ya existen no cambian."
    />
  );
}
