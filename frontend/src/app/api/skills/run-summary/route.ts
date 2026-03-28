/**
 * /api/skills/run-summary — proxy POST to Python backend /api/skills/run-summary
 */

import { NextRequest } from 'next/server';
import { proxyPost } from '@/lib/backend-proxy';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await proxyPost('/api/skills/run-summary', body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
