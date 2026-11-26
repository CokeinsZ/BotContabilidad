/**
 * Puerta de entrada a la API: importa desde aquí en hooks y en la sesión.
 *
 *   import { listarMeses, ApiError, type Planilla } from '@/api';
 */
export { ApiError, errorMessage, isNetworkError, isRetryable } from './client/errors';
export { refreshSession } from './client/refresh';
export { onSessionExpired, onSessionRefreshed } from './client/sessionEvents';
export { getTokens, onTokensChange, setTokens, type Tokens } from './client/tokens';

export { cerrarSesionEnServidor, consultarVinculacion, crearVinculacion } from './endpoints/auth.api';
export { listarComandos } from './endpoints/comandos.api';
export {
  cancelarSeleccion,
  enviarMensaje,
  obtenerEstadoChat,
  responderSeleccion,
  type MensajeSaliente,
} from './endpoints/mensajes.api';
export { actualizarAdministrador, actualizarNegocio, obtenerPerfil } from './endpoints/perfil.api';
export {
  crearOAbrirPlanilla,
  listarMeses,
  listarPlanillasDelMes,
  obtenerPlanilla,
  obtenerPlanillasDeHoy,
  obtenerResumenPlanilla,
} from './endpoints/planillas.api';
export { listarTrabajadores, obtenerNomina, obtenerTrabajador } from './endpoints/trabajadores.api';

export type * from './entities';
