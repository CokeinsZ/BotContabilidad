import { colors } from '@/theme';

import { EmptyState } from './EmptyState';

export interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  compact?: boolean;
  title?: string;
}

export function ErrorState({ message, onRetry, compact, title = 'No se pudo cargar' }: ErrorStateProps) {
  return (
    <EmptyState
      icon="error"
      iconColor={colors.status.danger.icon}
      title={title}
      message={message}
      compact={compact}
      action={onRetry ? { label: 'Reintentar', onPress: onRetry, icon: 'corregir_saldos' } : undefined}
    />
  );
}
