/**
 * /api/agents/run — proxy POST to Python backend /api/agents/run
 */

import { NextRequest } from 'next/server';
import { proxyPost } from '@/lib/backend-proxy';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await proxyPost('/api/agents/run', body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
