/**
 * /api/cron/cleanup-stale-runs — proxy POST to Python backend /api/cron/cleanup
 */

import { proxyPost } from '@/lib/backend-proxy';

export async function POST() {
  const res = await proxyPost('/api/cron/cleanup');
  return new Response(res.body, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
