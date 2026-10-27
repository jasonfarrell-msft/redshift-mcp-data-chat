import { ERRORS, LIMITS, type HealthState } from '../server/contracts.js';

export type ErrorCode = keyof typeof ERRORS | 'NETWORK';
export class ApiError extends Error {
  constructor(public code: ErrorCode, public turnsRemaining?: number) {
    super(code === 'NETWORK' ? 'Could not reach the app. Check your connection and try again.' : ERRORS[code]);
  }
}

export async function request<T>(route: string, body?: object, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(route, {
      method: body === undefined ? 'GET' : 'POST',
      credentials: 'same-origin',
      headers: body === undefined ? { Accept: 'application/json' } :
        { Accept: 'application/json', 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      signal: AbortSignal.any([AbortSignal.timeout(LIMITS.browserTimeoutMs), ...(signal ? [signal] : [])]),
    });
  } catch { throw new ApiError('NETWORK'); }
  let value: unknown;
  try { value = await response.json(); }
  catch { throw new ApiError('NETWORK'); }
  if (!response.ok) {
    if (route === '/api/health' && validHealth(value)) return value as T;
    const error = value as { error?: { code?: string }; turnsRemaining?: number } | null;
    const code = error?.error?.code;
    throw new ApiError(
      code && Object.hasOwn(ERRORS, code) ? code as keyof typeof ERRORS : 'NETWORK',
      typeof error?.turnsRemaining === 'number' ? error.turnsRemaining : undefined,
    );
  }
  return value as T;
}

export function validHealth(value: unknown): value is HealthState {
  if (!value || typeof value !== 'object') return false;
  const health = value as HealthState;
  return ['healthy', 'checking', 'stale', 'unavailable'].includes(health.status) &&
    (health.checkedAt === null || (typeof health.checkedAt === 'string' && Number.isFinite(Date.parse(health.checkedAt)))) &&
    (health.connected === null || typeof health.connected === 'boolean') &&
    (health.status !== 'healthy' || health.connected === true);
}

export function shouldSend(event: { key: string; shiftKey: boolean; nativeEvent: { isComposing?: boolean } }): boolean {
  return event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing;
}
