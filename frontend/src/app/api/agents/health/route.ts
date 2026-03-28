/**
 * /api/agents/health — proxy GET/POST to Python backend /api/agents/health
 */

import { NextRequest } from 'next/server';
import { proxyGet, proxyPost } from '@/lib/backend-proxy';

export async function GET() {
  const res = await proxyGet('/api/agents/health');
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await proxyPost('/api/agents/health', body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
