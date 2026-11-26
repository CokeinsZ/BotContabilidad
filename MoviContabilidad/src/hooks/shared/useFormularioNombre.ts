import { useRouter } from 'expo-router';
import { useForm, useWatch } from 'react-hook-form';

import { errorMessage, type Perfil } from '@/api';
import { useAlert, useToast } from '@/components/ui/feedback';
import type { FormularioNombreValores } from '@/components/domain/perfil';
import { limpiarNombre } from '@/utils/text/limpiarNombre';

/** Formulario de un nombre que se guarda en el bot y vuelve atrás (negocio y administrador). */
export function useFormularioNombre(
  nombreInicial: string,
  guardar: (nombre: string) => Promise<Perfil>,
) {
  const router = useRouter();
  const alert = useAlert();
  const toast = useToast();
  const form = useForm<FormularioNombreValores>({ defaultValues: { nombre: nombreInicial } });
  const nombre = useWatch({ control: form.control, name: 'nombre' });

  const onSubmit = form.handleSubmit(async (valores) => {
    try {
      await guardar(limpiarNombre(valores.nombre));
      toast.show('Guardado');
      router.back();
    } catch (error) {
      await alert.mostrar({ tipo: 'error', titulo: 'No se pudo guardar', mensaje: errorMessage(error) });
    }
  });

  return {
    control: form.control,
    onSubmit,
    guardando: form.formState.isSubmitting,
    puedeGuardar: limpiarNombre(nombre) !== limpiarNombre(nombreInicial),
  };
}
