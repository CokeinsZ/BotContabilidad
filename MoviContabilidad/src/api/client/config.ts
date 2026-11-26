import { APP } from '@/constants/app';
import { env } from '@/config/env';

/** Base de la API de la app en el bot. */
export const API_BASE_URL = `${env.apiUrl}/app`;
export const DEFAULT_TIMEOUT_MS = APP.requestTimeoutMs;
export const CHAT_TIMEOUT_MS = APP.chatTimeoutMs;
