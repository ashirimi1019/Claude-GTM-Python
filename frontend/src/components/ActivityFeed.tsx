'use client';

import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  Play,
  XCircle,
  Shield,
  Zap,
  Heart,
  Mail,
  Users,
  Brain,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ActivityFeedProps {
  campaignSlug: string;
}

interface AuditEntry {
  id: string;
  agent_id: string;
  action: string;
  severity: string;
  confidence: string;
  reason: string;
  details: string | null;
  params: Record<string, unknown>;
  status: string;
  applied_by: string | null;
  applied_at: string | null;
  rejection_reason: string | null;
  action_result: Record<string, unknown> | null;
  triggered_by: string;
  run_id: string | null;
  created_at: string;
}

function getStatusBadge(status: string) {
  switch (status) {
    case 'auto-applied':
      return { label: 'Auto-applied', icon: Zap, color: 'indigo' };
    case 'approved':
      return { label: 'Approved', icon: CheckCircle2, color: 'emerald' };
    case 'rejected':
      return { label: 'Rejected', icon: XCircle, color: 'red' };
    case 'pending':
      return { label: 'Pending', icon: Clock, color: 'amber' };
    default:
      return { label: status, icon: Shield, color: 'neutral' };
  }
}

function getActionIcon(action: string) {
  if (action.startsWith('run-skill')) return Play;
  if (action.includes('pause')) return Shield;
  if (action.includes('health')) return Heart;
  if (action.includes('reply') || action.includes('positive')) return Mail;
  if (action.includes('enrollment')) return Users;
  if (action.includes('deliverability')) return AlertTriangle;
  return Brain;
}

function getAgentLabel(agentId: string) {
  switch (agentId) {
    case 'orchestrator': return 'Orchestrator';
    case 'icp-tuner': return 'ICP Tuner';
    case 'copy-optimizer': return 'Copy Optimizer';
    case 'lead-quality': return 'Lead Quality';
    case 'health-monitor': return 'Health Monitor';
    default: return agentId;
  }
}

function getAgentColor(agentId: string) {
  switch (agentId) {
    case 'orchestrator': return 'indigo';
    case 'icp-tuner': return 'purple';
    case 'copy-optimizer': return 'amber';
    case 'lead-quality': return 'emerald';
    case 'health-monitor': return 'rose';
    default: return 'neutral';
  }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - Date.parse(dateStr);
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function FeedItem({ entry, isLast }: { entry: AuditEntry; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const badge = getStatusBadge(entry.status);
  const ActionIcon = getActionIcon(entry.action);
  const StatusIcon = badge.icon;
  const agentColor = getAgentColor(entry.agent_id);
  const execStatus = entry.action_result?.execution_status as string | undefined;

  return (
    <div className="relative">
      {/* Timeline connector */}
      {!isLast && (
        <div className="absolute left-[15px] top-8 bottom-0 w-px bg-neutral-800" />
      )}

      <div className="flex gap-3">
        {/* Timeline dot */}
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border',
          entry.severity === 'critical' && 'bg-red-500/10 border-red-500/30',
          entry.severity === 'warning' && 'bg-amber-500/10 border-amber-500/30',
          entry.severity === 'info' && 'bg-neutral-800 border-neutral-700',
        )}>
          <ActionIcon className={cn(
            'w-3.5 h-3.5',
            entry.severity === 'critical' && 'text-red-400',
            entry.severity === 'warning' && 'text-amber-400',
            entry.severity === 'info' && 'text-neutral-400',
          )} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pb-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full text-left group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={cn(
                    'text-xs px-1.5 py-0.5 rounded font-medium',
                    agentColor === 'indigo' && 'bg-indigo-500/10 text-indigo-400',
                    agentColor === 'purple' && 'bg-purple-500/10 text-purple-400',
                    agentColor === 'amber' && 'bg-amber-500/10 text-amber-400',
                    agentColor === 'emerald' && 'bg-emerald-500/10 text-emerald-400',
                    agentColor === 'rose' && 'bg-rose-500/10 text-rose-400',
                    agentColor === 'neutral' && 'bg-neutral-700/50 text-neutral-400',
                  )}>
                    {getAgentLabel(entry.agent_id)}
                  </span>

                  <span className={cn(
                    'flex items-center gap-1 text-xs px-1.5 py-0.5 rounded',
                    badge.color === 'indigo' && 'bg-indigo-500/10 text-indigo-400',
                    badge.color === 'emerald' && 'bg-emerald-500/10 text-emerald-400',
                    badge.color === 'red' && 'bg-red-500/10 text-red-400',
                    badge.color === 'amber' && 'bg-amber-500/10 text-amber-400',
                    badge.color === 'neutral' && 'bg-neutral-700/50 text-neutral-400',
                  )}>
                    <StatusIcon className="w-3 h-3" />
                    {badge.label}
                  </span>

                  {execStatus && execStatus !== 'applied' && (
                    <span className={cn(
                      'text-[10px] px-1.5 py-0.5 rounded font-mono',
                      execStatus === 'dispatched' && 'bg-blue-500/10 text-blue-400',
                      execStatus === 'failed' && 'bg-red-500/10 text-red-400',
                      execStatus === 'failed-dispatch' && 'bg-red-500/10 text-red-400',
                      execStatus === 'blocked-budget' && 'bg-orange-500/10 text-orange-400',
                      execStatus === 'blocked-health' && 'bg-orange-500/10 text-orange-400',
                    )}>
                      {execStatus}
                    </span>
                  )}
                </div>

                <p className="text-sm text-neutral-300 mt-1 leading-snug">
                  {entry.reason}
                </p>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0">
                <span className="text-[10px] text-neutral-600 whitespace-nowrap">
                  {timeAgo(entry.created_at)}
                </span>
                {expanded ? (
                  <ChevronDown className="w-3 h-3 text-neutral-600" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-neutral-600 group-hover:text-neutral-400" />
                )}
              </div>
            </div>
          </button>

          {expanded && (
            <div className="mt-2 space-y-2 text-xs">
              {entry.details && entry.details !== entry.reason && (
                <p className="text-neutral-500">{entry.details}</p>
              )}
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-neutral-600">
                <span>Action: <span className="text-neutral-400 font-mono">{entry.action}</span></span>
                <span>Confidence: <span className="text-neutral-400">{entry.confidence}</span></span>
                <span>Trigger: <span className="text-neutral-400">{entry.triggered_by}</span></span>
                {entry.applied_by && (
                  <span>By: <span className="text-neutral-400">{entry.applied_by}</span></span>
                )}
                {entry.rejection_reason && (
                  <span>Reason: <span className="text-red-400">{entry.rejection_reason}</span></span>
                )}
              </div>
              {entry.action_result && (
                <div className="bg-neutral-950/50 rounded px-2 py-1.5 font-mono text-[10px] text-neutral-500 overflow-x-auto">
                  {JSON.stringify(entry.action_result, null, 2)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ActivityFeed({ campaignSlug }: ActivityFeedProps) {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadActivity();
  }, [campaignSlug]);

  async function loadActivity() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/agents/approve?campaignSlug=${encodeURIComponent(campaignSlug)}&history=true&limit=100`,
      );
      if (!res.ok) throw new Error('Failed to load activity');
      const { history } = await res.json();
      setEntries(history ?? []);
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
        Loading activity...
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

  if (entries.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-500">
        <Clock className="w-8 h-8 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No activity yet.</p>
        <p className="text-xs mt-1 text-neutral-600">Run agents or wait for the daily cron to generate activity.</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {entries.map((entry, i) => (
        <FeedItem key={entry.id} entry={entry} isLast={i === entries.length - 1} />
      ))}
    </div>
  );
}
