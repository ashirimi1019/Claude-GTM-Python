/**
 * Standardised HTTP error types for all API routes.
 * Using this throughout the route layer ensures consistent error shapes client-side.
 */
import { NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

export interface ApiErrorBody {
  error: string;
  code: string;
  fields?: Record<string, string[]>;
}

export class AppError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly fields?: Record<string, string[]>,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

/** Send a structured 400 validation error */
export function validationError(fields: Record<string, string[]>): NextResponse {
  return NextResponse.json(
    { error: 'Invalid request', code: 'VALIDATION_ERROR', fields } satisfies ApiErrorBody,
    { status: 400 },
  );
}

/** Coerce unknown thrown values into a typed AppError — prevents raw primitives reaching errorResponse() */
export function toAppError(err: unknown): AppError {
  if (err instanceof AppError) return err;
  if (err instanceof Error) return new AppError(500, 'INTERNAL_ERROR', err.message);
  return new AppError(500, 'INTERNAL_ERROR', String(err));
}

/** Convert any thrown error to a NextResponse */
export function errorResponse(err: unknown): NextResponse {
  if (err instanceof AppError) {
    return NextResponse.json(
      { error: err.message, code: err.code, ...(err.fields ? { fields: err.fields } : {}) } satisfies ApiErrorBody,
      { status: err.status },
    );
  }
  // Unknown exception — log server-side, return generic 500 (never leak internals)
  logger.error({ err }, 'errorResponse received non-AppError');
  return NextResponse.json(
    { error: 'Internal server error', code: 'INTERNAL_ERROR' } satisfies ApiErrorBody,
    { status: 500 },
  );
}
