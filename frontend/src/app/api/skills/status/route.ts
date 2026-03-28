/**
 * /api/skills/status — proxy GET to Python backend /api/skills/status
 */

import { NextRequest } from 'next/server';
import { proxyGet } from '@/lib/backend-proxy';

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams.toString();
  const res = await proxyGet(`/api/skills/status?${params}`);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
