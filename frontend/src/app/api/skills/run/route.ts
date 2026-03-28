/**
 * /api/skills/run
 *
 * SSE proxy — queues a skill on the Python backend then pipes the SSE stream
 * back to the browser. The frontend's useSkillRunner hook connects to this
 * endpoint via EventSource, so the interface is identical to the original.
 *
 * Query params:
 *   skill    = 1-6 (required)
 *   offer    = offer slug (required)
 *   campaign = campaign slug (optional)
 *   formData = JSON-encoded form answers (skills 1-2)
 */

import { NextRequest } from 'next/server';
import { backendUrl } from '@/lib/backend-proxy';

export const maxDuration = 300;

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const skill = searchParams.get('skill');
  const offer = searchParams.get('offer');
  const campaign = searchParams.get('campaign') || '';
  const formData = searchParams.get('formData') || '';

  if (!skill || !offer) {
    return new Response(
      JSON.stringify({ error: 'Missing required params: skill, offer' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } },
    );
  }

  // 1. Queue the skill on the Python backend
  try {
    const queueRes = await fetch(backendUrl('/api/skills/run'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        skill_id: parseInt(skill, 10),
        offer_slug: offer,
        campaign_slug: campaign || undefined,
        form_data: formData ? JSON.parse(formData) : undefined,
      }),
    });

    if (!queueRes.ok) {
      const text = await queueRes.text();
      return new Response(
        JSON.stringify({ error: `Backend rejected skill run: ${text}` }),
        { status: queueRes.status, headers: { 'Content-Type': 'application/json' } },
      );
    }
  } catch (e) {
    return new Response(
      JSON.stringify({ error: `Failed to queue skill on backend: ${e}` }),
      { status: 502, headers: { 'Content-Type': 'application/json' } },
    );
  }

  // 2. Open SSE stream from the Python backend
  const streamParams = new URLSearchParams({ offer, skill });
  if (campaign) streamParams.set('campaign', campaign);

  const streamUrl = backendUrl(`/api/skills/stream?${streamParams.toString()}`);

  let upstream: Response;
  try {
    upstream = await fetch(streamUrl);
  } catch (e) {
    return new Response(
      JSON.stringify({ error: `Failed to connect to skill stream: ${e}` }),
      { status: 502, headers: { 'Content-Type': 'application/json' } },
    );
  }

  if (!upstream.ok || !upstream.body) {
    return new Response(
      JSON.stringify({ error: 'Failed to connect to skill stream' }),
      { status: 502, headers: { 'Content-Type': 'application/json' } },
    );
  }

  // 3. Pipe the SSE stream back to the browser
  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
