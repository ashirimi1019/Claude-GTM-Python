/**
 * /api/campaigns/[id]/icp-profile — proxy GET/POST to Python backend /api/icp/{campaign_id}
 */

import { NextRequest } from 'next/server';
import { proxyGet, proxyPost } from '@/lib/backend-proxy';

type RouteContext = { params: Promise<{ id: string }> };

export async function GET(_req: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const res = await proxyGet(`/api/icp/${id}`);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function POST(req: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  const body = await req.json();
  const res = await proxyPost(`/api/icp/${id}`, body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
