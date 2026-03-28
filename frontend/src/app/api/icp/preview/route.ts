/**
 * /api/icp/preview — proxy POST to Python backend /api/icp/{campaign_id}/preview
 */

import { NextRequest } from 'next/server';
import { proxyPost } from '@/lib/backend-proxy';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const campaignId = body.campaign_id;
  if (!campaignId) {
    return new Response(JSON.stringify({ error: 'Missing campaign_id' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  const res = await proxyPost(`/api/icp/${campaignId}/preview`, body);
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
