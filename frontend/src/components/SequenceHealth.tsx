'use client';

import { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Heart,
  Loader2,
  PauseCircle,
  TrendingUp,
  Users,
  Mail,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SequenceHealthProps {
  campaignSlug: string;
}

interface HealthEntry {
  id: string;
  action: string;
  params: Record<string, unknown>;
  created_at: string;
  severity: string;
}

interface SequenceData {
  sequenceId: string;
  sequenceName: string;
  status: string;
  contactsEnrolled: number;
  metrics: {
    open_rate: number;
    reply_rate: number;
    bounce_rate: number;
    emails_sent: number;
    contacts_count: number;
  } | null;
  pausedReason: string | null;
  enrollmentProgress: {
    total: number;
    enrolled: number;
    status: string;
    currentBatch: number;
  } | null;
  replyBreakdown: {
    positive: number;
    negative: number;
    ooo: number;
    unsubscribe: number;
    neutral: number;
  };
}

function RateGauge({ label, value, thresholds }: {
  label: string;
  value: number;
  thresholds: { good: number; warn: number; direction: 'above' | 'below' };
}) {
  const pct = Math.min(value, 100);
  let color = 'emerald';
  if (thresholds.direction === 'above') {
    if (value >= thresholds.warn) color = 'red';
    else if (value >= thresholds.good) color = 'amber';
  } else {
    if (value <= thresholds.warn) color = 'red';
    else if (value <= thresholds.good) color = 'amber';
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-neutral-400">{label}</span>
        <span className={cn(
          'font-mono font-medium',
          color === 'emerald' && 'text-emerald-400',
          color === 'amber' && 'text-amber-400',
          color === 'red' && 'text-red-400',
        )}>
          {value.toFixed(1)}%
        </span>
      </div>
      <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all',
            color === 'emerald' && 'bg-emerald-500',
            color === 'amber' && 'bg-amber-500',
            color === 'red' && 'bg-red-500',
          )}
          style={{ width: `${Math.max(pct, 1)}%` }}
        />
      </div>
    </div>
  );
}

export default function SequenceHealth({ campaignSlug }: SequenceHealthProps) {
  const [sequences, setSequences] = useState<SequenceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHealthData();
  }, [campaignSlug]);

  async function loadHealthData() {
    setLoading(true);
    setError(null);
    try {
      // Load health check audit entries + sequence data
      const res = await fetch(`/api/agents/approve?campaignSlug=${encodeURIComponent(campaignSlug)}&history=true&limit=200`);
      if (!res.ok) throw new Error('Failed to load health data');
      const { history } = await res.json();

      // Extract health-check entries (latest per sequence)
      const healthChecks = (history as HealthEntry[]).filter((h) => h.action === 'health-check');
      const replyClassifications = (history as HealthEntry[]).filter((h) => h.action === 'reply-classification');

      // Build sequence map from health checks
      const seqMap = new Map<string, SequenceData>();

      for (const hc of healthChecks) {
        const seqId = hc.params.apollo_sequence_id as string;
        if (!seqId || seqMap.has(seqId)) continue; // Only take latest per sequence

        const counts = { positive: 0, negative: 0, ooo: 0, unsubscribe: 0, neutral: 0 };
        // Find reply classification for this sequence
        const rc = replyClassifications.find(
          (r) => (r.params.apollo_sequence_id as string) === seqId,
        );
        if (rc?.params.counts) {
          const c = rc.params.counts as Record<string, number>;
          counts.positive = c.positive || 0;
          counts.negative = c.negative || 0;
          counts.ooo = c.ooo || 0;
          counts.unsubscribe = c.unsubscribe || 0;
          counts.neutral = c.neutral || 0;
        }

        seqMap.set(seqId, {
          sequenceId: seqId,
          sequenceName: (hc.params.sequence_name as string) || seqId,
          status: (hc.params.sequence_status as string) || 'unknown',
          contactsEnrolled: (hc.params.contacts_count as number) || 0,
          metrics: {
            open_rate: (hc.params.open_rate as number) || 0,
            reply_rate: (hc.params.reply_rate as number) || 0,
            bounce_rate: (hc.params.bounce_rate as number) || 0,
            emails_sent: (hc.params.emails_sent as number) || 0,
            contacts_count: (hc.params.contacts_count as number) || 0,
          },
          pausedReason: null,
          enrollmentProgress: null,
          replyBreakdown: counts,
        });
      }

      // Check for paused sequences
      const pauseEntries = (history as HealthEntry[]).filter((h) => h.action === 'pause-sequence');
      for (const pe of pauseEntries) {
        const seqId = pe.params.apollo_sequence_id as string;
        const seq = seqMap.get(seqId);
        if (seq) {
          seq.status = 'paused';
          seq.pausedReason = `Bounce rate ${((pe.params.bounce_rate as number) || 0).toFixed(1)}%`;
        }
      }

      setSequences(Array.from(seqMap.values()));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-neutral-500">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Loading health data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 py-8 px-4 text-red-400 bg-red-500/5 rounded-lg border border-red-500/20">
        <AlertTriangle className="w-4 h-4" />
        {error}
      </div>
    );
  }

  if (sequences.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-500">
        <Heart className="w-8 h-8 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No health data yet.</p>
        <p className="text-xs mt-1 text-neutral-600">Health monitor runs every 6 hours for campaigns with active sequences.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sequences.map((seq) => (
        <div key={seq.sequenceId} className="bg-neutral-900 rounded-lg border border-neutral-800 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              <span className="text-sm font-medium text-neutral-200 truncate max-w-[300px]">
                {seq.sequenceName}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {seq.status === 'paused' ? (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-500/10 border border-red-500/30 text-red-400">
                  <PauseCircle className="w-3 h-3" />
                  Paused
                </span>
              ) : seq.status === 'active' ? (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" />
                  Active
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-xs bg-neutral-700/50 border border-neutral-600 text-neutral-400">
                  {seq.status}
                </span>
              )}
            </div>
          </div>

          {/* Paused reason */}
          {seq.pausedReason && (
            <div className="px-4 py-2 bg-red-500/5 border-b border-red-500/20 text-xs text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-3 h-3 flex-shrink-0" />
              Auto-paused: {seq.pausedReason}. Manual resume required.
            </div>
          )}

          {/* Metrics */}
          {seq.metrics && (
            <div className="px-4 py-3 space-y-3">
              {/* Stats row */}
              <div className="flex items-center gap-4 text-xs text-neutral-400">
                <span className="flex items-center gap-1">
                  <Mail className="w-3 h-3" />
                  {seq.metrics.emails_sent} sent
                </span>
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {seq.metrics.contacts_count} contacts
                </span>
              </div>

              {/* Rate gauges */}
              <div className="grid grid-cols-3 gap-4">
                <RateGauge
                  label="Open Rate"
                  value={seq.metrics.open_rate}
                  thresholds={{ good: 30, warn: 10, direction: 'below' }}
                />
                <RateGauge
                  label="Reply Rate"
                  value={seq.metrics.reply_rate}
                  thresholds={{ good: 5, warn: 1, direction: 'below' }}
                />
                <RateGauge
                  label="Bounce Rate"
                  value={seq.metrics.bounce_rate}
                  thresholds={{ good: 3, warn: 5, direction: 'above' }}
                />
              </div>

              {/* Reply breakdown */}
              {Object.values(seq.replyBreakdown).some((v) => v > 0) && (
                <div className="pt-2 border-t border-neutral-800">
                  <div className="flex items-center gap-1 text-xs text-neutral-500 mb-2">
                    <BarChart3 className="w-3 h-3" />
                    Reply Classification
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {seq.replyBreakdown.positive > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                        {seq.replyBreakdown.positive} positive
                      </span>
                    )}
                    {seq.replyBreakdown.negative > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-red-500/10 border border-red-500/20 text-red-400">
                        {seq.replyBreakdown.negative} negative
                      </span>
                    )}
                    {seq.replyBreakdown.ooo > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-amber-500/10 border border-amber-500/20 text-amber-400">
                        {seq.replyBreakdown.ooo} OOO
                      </span>
                    )}
                    {seq.replyBreakdown.unsubscribe > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-orange-500/10 border border-orange-500/20 text-orange-400">
                        {seq.replyBreakdown.unsubscribe} unsubscribe
                      </span>
                    )}
                    {seq.replyBreakdown.neutral > 0 && (
                      <span className="px-2 py-0.5 rounded text-xs bg-neutral-500/10 border border-neutral-500/20 text-neutral-400">
                        {seq.replyBreakdown.neutral} neutral
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Enrollment progress */}
              {seq.enrollmentProgress && (
                <div className="pt-2 border-t border-neutral-800">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-neutral-500 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      Enrollment Progress
                    </span>
                    <span className="text-neutral-400 font-mono">
                      {seq.enrollmentProgress.enrolled}/{seq.enrollmentProgress.total}
                    </span>
                  </div>
                  <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all"
                      style={{
                        width: `${Math.max(
                          (seq.enrollmentProgress.enrolled / seq.enrollmentProgress.total) * 100,
                          1,
                        )}%`,
                      }}
                    />
                  </div>
                  <div className="text-[10px] text-neutral-600 mt-1">
                    Batch {seq.enrollmentProgress.currentBatch} · {seq.enrollmentProgress.status}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
