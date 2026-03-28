/**
 * /api/artifacts/[id] — proxy GET to Python backend /api/artifacts/{path}
 */

import { NextRequest } from 'next/server';
import { proxyGet } from '@/lib/backend-proxy';

type RouteContext = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const res = await proxyGet(`/api/artifacts/${id}`);
  const contentType = res.headers.get('Content-Type') || 'application/octet-stream';
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': contentType },
  });
}
