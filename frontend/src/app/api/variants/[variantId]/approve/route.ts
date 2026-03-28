/**
 * /api/variants/[variantId]/approve — proxy POST to Python backend /api/variants/{id}/approve
 */

import { NextRequest } from 'next/server';
import { proxyPost } from '@/lib/backend-proxy';

type RouteContext = { params: Promise<{ variantId: string }> };

export async function POST(_req: NextRequest, context: RouteContext) {
  const { variantId } = await context.params;
  const res = await proxyPost(`/api/variants/${variantId}/approve`);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
