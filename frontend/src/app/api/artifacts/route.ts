/**
 * /api/artifacts — proxy GET to Python backend /api/artifacts
 */

import { NextRequest } from 'next/server';
import { proxyGet } from '@/lib/backend-proxy';

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams.toString();
  const res = await proxyGet(`/api/artifacts?${params}`);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
