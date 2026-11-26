import { useComandos } from '@/hooks/data/comandos/useComandos';

export function useAyudaScreen() {
  const { comandos } = useComandos();
  return { comandos };
}
