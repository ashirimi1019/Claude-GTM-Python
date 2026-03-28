/**
 * Frontend logger — console wrapper with the same call-site API as the pino backend logger.
 * Uses console.* instead of pino to remain compatible with Next.js edge runtime.
 *
 * Usage (identical to backend logger):
 *   logger.info({ fn: 'myFn', route: '/api/skills/run' }, 'Skill started');
 *   logger.error({ fn: 'myFn', err }, 'Fatal error');
 */

type LogFields = Record<string, unknown>;

function serialize(fields: LogFields): string {
  return Object.entries(fields)
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(' ');
}

export const logger = {
  info:  (fields: LogFields, msg: string) => console.info(`[INFO]  ${msg} ${serialize(fields)}`),
  warn:  (fields: LogFields, msg: string) => console.warn(`[WARN]  ${msg} ${serialize(fields)}`),
  error: (fields: LogFields, msg: string) => console.error(`[ERROR] ${msg} ${serialize(fields)}`),
  debug: (fields: LogFields, msg: string) => console.debug(`[DEBUG] ${msg} ${serialize(fields)}`),
};
