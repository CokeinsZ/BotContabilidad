import { useCallback } from 'react';

import { useToast } from '@/components/ui/feedback';
import { abrirEnGoogleSheets } from '@/utils/linking/googleSheets';

export function useAbrirEnGoogleSheets() {
  const toast = useToast();
  return useCallback(
    (url: string) => {
      abrirEnGoogleSheets(url).catch(() => toast.show('No se pudo abrir Google Sheets.', 'danger'));
    },
    [toast],
  );
}
