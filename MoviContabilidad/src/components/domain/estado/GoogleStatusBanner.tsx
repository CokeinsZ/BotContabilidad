import { Banner } from '@/components/ui/feedback';

/** Hoy el bot responde "el servidor aún no está autenticado con Google" en cada comando; aquí se avisa antes. */
export function GoogleStatusBanner({ conectado }: { conectado: boolean }) {
  if (conectado) return null;
  return (
    <Banner
      tone="warning"
      title="El servidor no está conectado con Google"
      message="No se pueden leer ni escribir planillas hasta que el proveedor del bot lo conecte."
    />
  );
}
