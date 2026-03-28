/**
 * /api/agents/config — proxy GET/POST to Python backend /api/agents/config
 */

import { NextRequest } from 'next/server';
import { proxyGet, proxyPost } from '@/lib/backend-proxy';

export async function GET() {
  const res = await proxyGet('/api/agents/config');
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await proxyPost('/api/agents/config', body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
