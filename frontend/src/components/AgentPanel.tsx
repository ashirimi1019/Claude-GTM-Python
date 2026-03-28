'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Target,
  Wrench,
  PenLine,
  Search,
  ChevronDown,
  ChevronRight,
  Zap,
  Settings,
  Clock,
  Shield,
  ShieldCheck,
  ShieldOff,
  Check,
  X,
  Play,
  Pause,
  History,
  Heart,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import SequenceHealth from './SequenceHealth';
import ActivityFeed from './ActivityFeed';

type AgentTab = 'analysis' | 'health' | 'activity';

// ─── Types ───────────────────────────────────────────

interface AgentRecommendation {
  agentId: string;
  action: string;
  confidence: 'high' | 'medium' | 'low';
  severity: 'info' | 'warning' | 'critical';
  reason: string;
  details: string;
  params: Record<string, unknown>;
  requiresApproval: boolean;
  createdAt: string;
}

interface AgentRunResult {
  agentId: string;
  recommendations: AgentRecommendation[];
  analysisNotes: string[];
  durationMs: number;
  warnings: string[];
}

interface CampaignSnapshot {
  totalSearchCandidates: number | null;
  stage1Shortlisted: number | null;
  stage1QualRate: number | null;
  enrichRate: number | null;
  stage2Qualified: number | null;
  rejectedAfterEnrichment: number | null;
  finalQualRate: number | null;
  emailsSent: number;
  openRate: number | null;
  replyRate: number | null;
  bounceRate: number | null;
  positiveReplies: number;
  negativeReplies: number;
  contactsEnrolled: number;
  sequencesActive: number;
  daysSinceLaunch: number;
  strictnessLevel: string | null;
  hasIcpProfile: boolean;
}

interface ConflictResolutionSummary {
  winner: string;
  loser: string;
  rule: string;
  explanation: string;
}

interface DeferredActionSummary {
  agentId: string;
  action: string;
  domain: string;
  reason: string;
}

interface AgentResponse {
  results: AgentRunResult[];
  snapshot: CampaignSnapshot;
  totalRecommendations: number;
  criticalCount: number;
  runId: string;
  autoAppliedCount: number;
  pendingCount: number;
  autonomyEnabled: boolean;
  // V2 coordination metadata (optional for backward compat)
  coordinationVersion?: number;
  conflictsDetected?: number;
  conflictResolutions?: ConflictResolutionSummary[];
  skippedAgents?: string[];
  deferredCount?: number;
  deferredActions?: DeferredActionSummary[];
}

interface AgentConfig {
  campaignId: string;
  enabled: boolean;
  scheduleCron: string;
  agentsEnabled: string[];
  autoApplyRules: Record<string, boolean>;
  paused: boolean;
  pausedReason: string | null;
  lastRunAt: string | null;
  dailyBudgetApolloCredits: number;
  dailyBudgetOpenaiCents: number;
  exists: boolean;
}

interface PendingAction {
  id: string;
  agent_id: string;
  action: string;
  severity: string;
  confidence: string;
  reason: string;
  details: string;
  params: Record<string, unknown>;
  status: string;
  triggered_by: string;
  run_id: string;
  created_at: string;
}

// ─── Constants ───────────────────────────────────────

const AGENT_META: Record<string, { name: string; icon: React.ReactNode; color: string }> = {
  orchestrator: { name: 'Orchestrator', icon: <Target className="h-4 w-4" />, color: 'text-blue-400' },
  'icp-tuner': { name: 'ICP Tuner', icon: <Wrench className="h-4 w-4" />, color: 'text-amber-400' },
  'copy-optimizer': { name: 'Copy Optimizer', icon: <PenLine className="h-4 w-4" />, color: 'text-purple-400' },
  'lead-quality': { name: 'Lead Quality', icon: <Search className="h-4 w-4" />, color: 'text-emerald-400' },
};

const SEVERITY_CONFIG = {
  critical: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500' },
  warning: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-500' },
  info: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-500' },
};

// Safe actions that can be auto-applied without risk
const SAFE_ACTIONS = [
  'flag-false-positive', 'flag-missed-opportunity', 'generate-new-variant',
  'promote-winner', 'alert-operator', 'wait-for-data', 'skip-skill', 'none',
];

// Risky actions that need human review by default
const RISKY_ACTIONS = [
  'relax-strictness', 'tighten-strictness', 'adjust-threshold',
  'pause-underperformer', 'adjust-subject-line', 'shorten-body',
  'add-industry-exclusion', 'add-tech-keyword', 'widen-size-range',
  'run-skill', 'recommend-filter-change', 'reclassify-company',
  'remove-tech-keyword',
];

const ACTION_LABELS: Record<string, string> = {
  'flag-false-positive': 'Flag false positives',
  'flag-missed-opportunity': 'Flag missed opportunities',
  'generate-new-variant': 'Generate new copy variant',
  'promote-winner': 'Promote winning variant',
  'alert-operator': 'Alert operator',
  'wait-for-data': 'Wait for data',
  'skip-skill': 'Skip skill',
  'none': 'No action',
  'relax-strictness': 'Relax ICP strictness',
  'tighten-strictness': 'Tighten ICP strictness',
  'adjust-threshold': 'Adjust ICP threshold',
  'pause-underperformer': 'Pause underperforming sequences',
  'adjust-subject-line': 'Adjust subject lines',
  'shorten-body': 'Shorten email body',
  'add-industry-exclusion': 'Add industry exclusion',
  'add-tech-keyword': 'Add tech keyword',
  'widen-size-range': 'Widen company size range',
  'run-skill': 'Run skill',
  'recommend-filter-change': 'Recommend filter change',
  'reclassify-company': 'Reclassify company',
  'remove-tech-keyword': 'Remove tech keyword',
};

// ─── Sub-components ──────────────────────────────────

function SnapshotBar({ snapshot }: { snapshot: CampaignSnapshot }) {
  const items = [
    { label: 'ICP', value: snapshot.hasIcpProfile ? (snapshot.strictnessLevel ?? 'set') : 'not set', ok: snapshot.hasIcpProfile },
    { label: 'Pipeline', value: snapshot.totalSearchCandidates != null ? `${snapshot.stage2Qualified ?? 0} qualified` : '—', ok: (snapshot.stage2Qualified ?? 0) > 0 },
    { label: 'Enrich', value: snapshot.enrichRate != null ? `${snapshot.enrichRate.toFixed(0)}%` : '—', ok: (snapshot.enrichRate ?? 0) >= 50 },
    { label: 'Emails', value: snapshot.emailsSent.toString(), ok: snapshot.emailsSent > 0 },
    { label: 'Days', value: snapshot.daysSinceLaunch.toString(), ok: true },
    { label: 'Sequences', value: snapshot.sequencesActive.toString(), ok: snapshot.sequencesActive > 0 },
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {items.map(({ label, value, ok }) => (
        <div
          key={label}
          className={cn(
            'px-2.5 py-1 rounded-lg text-xs border',
            ok ? 'bg-neutral-900 border-neutral-800 text-neutral-300' : 'bg-neutral-900 border-neutral-800 text-neutral-500',
          )}
        >
          <span className="text-neutral-500">{label}:</span>{' '}
          <span className="font-medium">{value}</span>
        </div>
      ))}
    </div>
  );
}

function RecommendationCard({
  rec,
  onApprove,
  onReject,
  auditId,
  showActions,
}: {
  rec: AgentRecommendation;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  auditId?: string;
  showActions?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const sev = SEVERITY_CONFIG[rec.severity];
  const agent = AGENT_META[rec.agentId];

  return (
    <div className={cn('border rounded-xl overflow-hidden', sev.border, sev.bg)}>
      <button
        type="button"
        className="w-full px-4 py-3 flex items-start gap-3 text-left"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={cn('w-2 h-2 rounded-full mt-1.5 shrink-0', sev.dot)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5 flex-wrap">
            <span className={cn('text-xs font-medium', agent?.color ?? 'text-neutral-400')}>
              {agent?.name ?? rec.agentId}
            </span>
            <span className="text-[10px] text-neutral-600">·</span>
            <code className="text-[10px] text-neutral-500 font-mono">{rec.action}</code>
            {rec.requiresApproval && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                needs approval
              </span>
            )}
          </div>
          <p className={cn('text-sm', sev.text)}>{rec.reason}</p>
        </div>
        <div className="shrink-0 mt-1">
          {expanded ? <ChevronDown className="h-3.5 w-3.5 text-neutral-500" /> : <ChevronRight className="h-3.5 w-3.5 text-neutral-500" />}
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-3 border-t border-neutral-800/50">
          <p className="text-xs text-neutral-400 mt-2 leading-relaxed">{rec.details}</p>
          <div className="flex items-center gap-3 mt-2 text-[10px] text-neutral-600">
            <span>Confidence: {rec.confidence}</span>
            <span>Severity: {rec.severity}</span>
          </div>
          {showActions && auditId && onApprove && onReject && (
            <div className="flex gap-2 mt-3">
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onApprove(auditId); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
              >
                <Check className="h-3 w-3" /> Approve
              </button>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onReject(auditId); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors"
              >
                <X className="h-3 w-3" /> Reject
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AgentSection({ result, skipped }: { result: AgentRunResult; skipped?: boolean }) {
  const [expanded, setExpanded] = useState(result.recommendations.length > 0 && !skipped);
  const agent = AGENT_META[result.agentId];
  const hasRecs = result.recommendations.length > 0;

  // Detect conflict-related warnings for inline display
  const conflictWarnings = result.warnings.filter(w => w.includes('[CONFLICT]'));
  const otherWarnings = result.warnings.filter(w => !w.includes('[CONFLICT]'));

  return (
    <div className={cn(
      'border rounded-xl overflow-hidden',
      skipped ? 'border-neutral-800/50 opacity-60' : 'border-neutral-800',
    )}>
      <button
        type="button"
        className="w-full px-4 py-3 flex items-center gap-3 text-left hover:bg-neutral-900/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className={skipped ? 'text-neutral-600' : (agent?.color ?? 'text-neutral-400')}>{agent?.icon}</span>
        <span className={cn('text-sm font-medium flex-1', skipped ? 'text-neutral-500' : 'text-neutral-200')}>
          {agent?.name ?? result.agentId}
        </span>
        {skipped ? (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-800 border border-neutral-700 text-neutral-500">
            skipped
          </span>
        ) : hasRecs ? (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400">
            {result.recommendations.length} rec{result.recommendations.length !== 1 ? 's' : ''}
          </span>
        ) : (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            healthy
          </span>
        )}
        {!skipped && <span className="text-[10px] text-neutral-600">{result.durationMs}ms</span>}
        {expanded ? <ChevronDown className="h-3.5 w-3.5 text-neutral-500" /> : <ChevronRight className="h-3.5 w-3.5 text-neutral-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-3 space-y-2 border-t border-neutral-800/50">
          {result.analysisNotes.map((note, i) => (
            <p key={i} className={cn(
              'text-xs mt-2',
              note.startsWith('[SKIPPED]') ? 'text-neutral-600 italic' :
              note.startsWith('[AUTO]') ? 'text-emerald-500/80' :
              'text-neutral-500',
            )}>{note}</p>
          ))}
          {result.recommendations.map((rec, i) => (
            <RecommendationCard key={i} rec={rec} />
          ))}
          {/* Conflict warnings — distinguished style */}
          {conflictWarnings.map((w, i) => (
            <div key={`cw-${i}`} className="flex items-start gap-2 text-xs text-red-400/70 mt-1">
              <Shield className="h-3 w-3 shrink-0 mt-0.5" />
              <span>{w.replace('[CONFLICT] ', '')}</span>
            </div>
          ))}
          {/* Regular warnings */}
          {otherWarnings.map((w, i) => (
            <div key={`ow-${i}`} className="flex items-start gap-2 text-xs text-amber-400/80 mt-1">
              <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Coordination Outcome Summary ────────────────────

function CoordinationSummary({ data }: { data: AgentResponse }) {
  const hasSkipped = (data.skippedAgents?.length ?? 0) > 0;
  const hasConflicts = (data.conflictsDetected ?? 0) > 0;
  const hasDeferred = (data.deferredCount ?? 0) > 0;

  if (!hasSkipped && !hasConflicts && !hasDeferred) return null;

  return (
    <div className="border border-neutral-800 rounded-xl overflow-hidden">
      <div className="px-4 py-2.5 flex items-center gap-2 border-b border-neutral-800/50 bg-neutral-900/50">
        <Shield className="h-3.5 w-3.5 text-neutral-400" />
        <span className="text-xs font-medium text-neutral-300">Coordination Decisions</span>
      </div>
      <div className="px-4 py-3 space-y-2.5">
        {/* Skipped agents */}
        {hasSkipped && (
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-neutral-600 mt-1.5 shrink-0" />
            <div className="text-xs">
              <span className="text-neutral-400">Skipped: </span>
              <span className="text-neutral-500">
                {data.skippedAgents!.map(id => AGENT_META[id]?.name ?? id).join(', ')}
              </span>
              <span className="text-neutral-600"> — disabled in config, produced no analysis</span>
            </div>
          </div>
        )}

        {/* Conflict resolutions */}
        {hasConflicts && data.conflictResolutions?.map((c, i) => {
          const isSafety = c.rule === 'safety-precedence';
          return (
            <div key={i} className="flex items-start gap-2">
              <div className={cn(
                'w-1.5 h-1.5 rounded-full mt-1.5 shrink-0',
                isSafety ? 'bg-red-500' : 'bg-amber-500',
              )} />
              <div className="text-xs">
                <span className={isSafety ? 'text-red-400' : 'text-amber-400'}>
                  {isSafety ? 'Safety override: ' : 'Suppressed: '}
                </span>
                <span className="text-neutral-400">{c.explanation}</span>
                <code className="text-[10px] text-neutral-600 ml-1">({c.rule})</code>
              </div>
            </div>
          );
        })}

        {/* Deferred actions */}
        {hasDeferred && data.deferredActions?.map((d, i) => {
          // Check if there's also a safety action from the same agent that was NOT deferred
          const safetyBypassed = data.results.some(r =>
            r.agentId === d.agentId &&
            r.recommendations.some(rec =>
              rec.action === 'pause-underperformer' || rec.action === 'pause-sequence',
            ),
          );

          return (
            <div key={`defer-${i}`} className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
              <div className="text-xs">
                <span className="text-blue-400">Deferred: </span>
                <span className="text-neutral-400">
                  {AGENT_META[d.agentId]?.name ?? d.agentId} → {ACTION_LABELS[d.action] ?? d.action}
                </span>
                <span className="text-neutral-600"> — {d.reason}</span>
                {safetyBypassed && (
                  <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400">
                    safety action still active
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Autonomy Settings Panel ─────────────────────────

function AutonomySettings({
  campaignSlug,
  config,
  onConfigChange,
}: {
  campaignSlug: string;
  config: AgentConfig;
  onConfigChange: (config: AgentConfig) => void;
}) {
  const [saving, setSaving] = useState(false);
  const [localRules, setLocalRules] = useState(config.autoApplyRules);

  useEffect(() => {
    setLocalRules(config.autoApplyRules);
  }, [config.autoApplyRules]);

  const saveConfig = async (updates: Partial<AgentConfig>) => {
    setSaving(true);
    try {
      const res = await fetch('/api/agents/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaignSlug, ...updates }),
      });
      if (res.ok) {
        onConfigChange({ ...config, ...updates, exists: true });
      }
    } finally {
      setSaving(false);
    }
  };

  const toggleRule = async (action: string) => {
    const newRules = { ...localRules, [action]: !localRules[action] };
    setLocalRules(newRules);
    await saveConfig({ autoApplyRules: newRules });
  };

  return (
    <div className="border border-neutral-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 flex items-center justify-between border-b border-neutral-800/50">
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-neutral-400" />
          <span className="text-sm font-medium text-neutral-200">Autonomy Settings</span>
        </div>
        {saving && <Loader2 className="h-3 w-3 animate-spin text-neutral-500" />}
      </div>

      <div className="p-4 space-y-4">
        {/* Master toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-neutral-200">Enable Autonomous Mode</p>
            <p className="text-xs text-neutral-500 mt-0.5">Agents run on schedule and auto-apply safe actions</p>
          </div>
          <button
            type="button"
            onClick={() => saveConfig({ enabled: !config.enabled })}
            className={cn(
              'relative w-11 h-6 rounded-full transition-colors',
              config.enabled ? 'bg-emerald-500' : 'bg-neutral-700',
            )}
          >
            <span
              className={cn(
                'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform',
                config.enabled ? 'translate-x-5' : 'translate-x-0',
              )}
            />
          </button>
        </div>

        {/* Kill switch */}
        {config.enabled && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {config.paused ? (
                <ShieldOff className="h-4 w-4 text-red-400" />
              ) : (
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
              )}
              <div>
                <p className="text-sm text-neutral-200">{config.paused ? 'Paused' : 'Active'}</p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  {config.paused ? 'All autonomy paused' : 'Agents will auto-apply approved actions'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => saveConfig({ paused: !config.paused })}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                config.paused
                  ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                  : 'bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20',
              )}
            >
              {config.paused ? <><Play className="h-3 w-3" /> Resume</> : <><Pause className="h-3 w-3" /> Pause All</>}
            </button>
          </div>
        )}

        {/* Last run info */}
        {config.lastRunAt && (
          <div className="flex items-center gap-2 text-xs text-neutral-500">
            <Clock className="h-3 w-3" />
            Last run: {new Date(config.lastRunAt).toLocaleString()}
          </div>
        )}

        {/* Auto-apply rules */}
        {config.enabled && !config.paused && (
          <div className="space-y-3">
            <p className="text-xs font-medium text-neutral-400 uppercase tracking-wider">Auto-Apply Rules</p>

            <div className="space-y-1">
              <p className="text-[10px] text-emerald-400 font-medium mb-1">Safe Actions (low risk)</p>
              {SAFE_ACTIONS.map((action) => (
                <div key={action} className="flex items-center justify-between py-1">
                  <span className="text-xs text-neutral-400">{ACTION_LABELS[action] ?? action}</span>
                  <button
                    type="button"
                    onClick={() => toggleRule(action)}
                    className={cn(
                      'relative w-9 h-5 rounded-full transition-colors',
                      localRules[action] ? 'bg-emerald-500' : 'bg-neutral-700',
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform',
                        localRules[action] ? 'translate-x-4' : 'translate-x-0',
                      )}
                    />
                  </button>
                </div>
              ))}
            </div>

            <div className="space-y-1">
              <p className="text-[10px] text-amber-400 font-medium mb-1">Risky Actions (require caution)</p>
              {RISKY_ACTIONS.map((action) => (
                <div key={action} className="flex items-center justify-between py-1">
                  <span className="text-xs text-neutral-400">{ACTION_LABELS[action] ?? action}</span>
                  <button
                    type="button"
                    onClick={() => toggleRule(action)}
                    className={cn(
                      'relative w-9 h-5 rounded-full transition-colors',
                      localRules[action] ? 'bg-amber-500' : 'bg-neutral-700',
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform',
                        localRules[action] ? 'translate-x-4' : 'translate-x-0',
                      )}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Pending Approvals Panel ─────────────────────────

function PendingApprovals({
  campaignSlug,
}: {
  campaignSlug: string;
}) {
  const [pending, setPending] = useState<PendingAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState<string | null>(null);

  const loadPending = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/agents/approve?campaignSlug=${encodeURIComponent(campaignSlug)}`);
      if (res.ok) {
        const data = await res.json();
        setPending(data.pending ?? []);
      }
    } finally {
      setLoading(false);
    }
  }, [campaignSlug]);

  useEffect(() => { loadPending(); }, [loadPending]);

  const handleDecision = async (auditId: string, decision: 'approve' | 'reject') => {
    setProcessing(auditId);
    try {
      const res = await fetch('/api/agents/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auditId, decision }),
      });
      if (res.ok) {
        setPending((prev) => prev.filter((p) => p.id !== auditId));
      }
    } finally {
      setProcessing(null);
    }
  };

  if (loading) {
    return (
      <div className="border border-neutral-800 rounded-xl p-6 text-center">
        <Loader2 className="h-4 w-4 animate-spin text-neutral-500 mx-auto" />
      </div>
    );
  }

  if (pending.length === 0) return null;

  return (
    <div className="border border-amber-500/20 rounded-xl overflow-hidden">
      <div className="px-4 py-3 flex items-center justify-between border-b border-amber-500/20 bg-amber-500/5">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-amber-300">
            {pending.length} Pending Approval{pending.length !== 1 ? 's' : ''}
          </span>
        </div>
        <button
          type="button"
          onClick={loadPending}
          className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
        >
          Refresh
        </button>
      </div>
      <div className="p-3 space-y-2">
        {pending.map((p) => (
          <div key={p.id} className="relative">
            {processing === p.id && (
              <div className="absolute inset-0 bg-neutral-900/80 rounded-xl flex items-center justify-center z-10">
                <Loader2 className="h-4 w-4 animate-spin text-neutral-400" />
              </div>
            )}
            <RecommendationCard
              rec={{
                agentId: p.agent_id,
                action: p.action,
                confidence: p.confidence as 'high' | 'medium' | 'low',
                severity: p.severity as 'info' | 'warning' | 'critical',
                reason: p.reason,
                details: p.details ?? '',
                params: p.params,
                requiresApproval: true,
                createdAt: p.created_at,
              }}
              auditId={p.id}
              showActions
              onApprove={(id) => handleDecision(id, 'approve')}
              onReject={(id) => handleDecision(id, 'reject')}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Panel ──────────────────────────────────────

interface AgentPanelProps {
  offerSlug: string;
  campaignSlug: string;
}

export function AgentPanel({ offerSlug, campaignSlug }: AgentPanelProps) {
  const [data, setData] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [activeTab, setActiveTab] = useState<AgentTab>('analysis');

  // Load config on mount
  useEffect(() => {
    fetch(`/api/agents/config?campaignSlug=${encodeURIComponent(campaignSlug)}`)
      .then((res) => res.json())
      .then((data) => setConfig(data))
      .catch(() => { /* config may not exist */ });
  }, [campaignSlug]);

  const runAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/agents/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ offerSlug, campaignSlug }),
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(errBody.error || `HTTP ${res.status}`);
      }
      const result: AgentResponse = await res.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run agents');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Brain className="h-4.5 w-4.5 text-purple-400" />
            AI Agents
            {config?.enabled && !config?.paused && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-normal">
                AUTONOMOUS
              </span>
            )}
            {config?.paused && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-normal">
                PAUSED
              </span>
            )}
          </h2>
          <p className="text-gray-500 text-xs mt-0.5">
            4 agents analyze your campaign and {config?.enabled ? 'auto-apply safe actions' : 'recommend next actions'}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            className={cn(
              'p-2 rounded-lg transition-colors',
              showSettings
                ? 'bg-neutral-800 text-neutral-200'
                : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/50',
            )}
            title="Autonomy Settings"
          >
            <Settings className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={runAgents}
            disabled={loading}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all',
              loading
                ? 'bg-neutral-800 text-neutral-500 cursor-not-allowed'
                : 'bg-purple-500/10 text-purple-300 border border-purple-500/30 hover:bg-purple-500/20 hover:text-purple-200',
            )}
          >
            {loading ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Analyzing...</>
            ) : (
              <><Zap className="h-3.5 w-3.5" /> Run All Agents</>
            )}
          </button>
        </div>
      </div>

      {/* Settings panel */}
      {showSettings && config && (
        <AutonomySettings
          campaignSlug={campaignSlug}
          config={config}
          onConfigChange={setConfig}
        />
      )}

      {/* Tab navigation */}
      <div className="flex items-center gap-1 border-b border-neutral-800">
        {([
          { key: 'analysis' as AgentTab, label: 'Analysis', icon: Brain },
          { key: 'health' as AgentTab, label: 'Health', icon: Heart },
          { key: 'activity' as AgentTab, label: 'Activity', icon: Activity },
        ]).map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors border-b-2 -mb-px',
              activeTab === tab.key
                ? 'border-purple-500 text-purple-300'
                : 'border-transparent text-neutral-500 hover:text-neutral-300',
            )}
          >
            <tab.icon className="w-3.5 h-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Analysis tab */}
      {activeTab === 'analysis' && (
        <>
          {/* Pending approvals */}
          <PendingApprovals campaignSlug={campaignSlug} />

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 px-4 py-3 bg-red-500/5 border border-red-500/20 rounded-xl text-sm text-red-400">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Empty state */}
          {!data && !loading && !error && (
            <div className="border border-dashed border-neutral-700 rounded-xl p-12 text-center">
              <Brain className="h-8 w-8 text-neutral-600 mx-auto mb-3" />
              <p className="text-neutral-400 text-sm mb-1">No agent analysis yet</p>
              <p className="text-neutral-500 text-xs">
                Click &quot;Run All Agents&quot; to get AI-powered recommendations for this campaign.
              </p>
            </div>
          )}

          {/* Results */}
          {data && (
            <>
              <SnapshotBar snapshot={data.snapshot} />

              {/* Summary banner */}
              <div
                className={cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl border',
                  data.criticalCount > 0
                    ? 'bg-red-500/5 border-red-500/20'
                    : data.totalRecommendations > 0
                      ? 'bg-amber-500/5 border-amber-500/20'
                      : 'bg-emerald-500/5 border-emerald-500/20',
                )}
              >
                {data.criticalCount > 0 ? (
                  <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
                ) : data.totalRecommendations > 0 ? (
                  <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                )}
                <span
                  className={cn(
                    'text-sm flex-1',
                    data.criticalCount > 0 ? 'text-red-400'
                      : data.totalRecommendations > 0 ? 'text-amber-400'
                        : 'text-emerald-400',
                  )}
                >
                  {data.totalRecommendations === 0
                    ? 'All agents report healthy status. No action needed.'
                    : `${data.totalRecommendations} recommendation${data.totalRecommendations !== 1 ? 's' : ''}${
                        data.criticalCount > 0 ? `, ${data.criticalCount} critical` : ''
                      }`}
                </span>
                {/* Auto-apply badge */}
                {data.autoAppliedCount > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 shrink-0">
                    {data.autoAppliedCount} auto-applied
                  </span>
                )}
                {data.pendingCount > 0 && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 shrink-0">
                    {data.pendingCount} pending
                  </span>
                )}
              </div>

              {/* Coordination decisions (skipped/suppressed/deferred) */}
              <CoordinationSummary data={data} />

              {/* Agent sections */}
              <div className="space-y-3">
                {data.results.map((result) => (
                  <AgentSection
                    key={result.agentId}
                    result={result}
                    skipped={data.skippedAgents?.includes(result.agentId)}
                  />
                ))}
              </div>

              {/* Run metadata */}
              <div className="flex items-center gap-3 text-[10px] text-neutral-600 flex-wrap">
                <History className="h-3 w-3" />
                <span>Run ID: {data.runId?.slice(0, 8)}</span>
                {data.coordinationVersion && <span>· v{data.coordinationVersion}</span>}
                {data.autonomyEnabled && <span>· Autonomy: ON</span>}
                {(data.conflictsDetected ?? 0) > 0 && (
                  <span>· {data.conflictsDetected} conflict{data.conflictsDetected !== 1 ? 's' : ''} resolved</span>
                )}
                {(data.deferredCount ?? 0) > 0 && (
                  <span>· {data.deferredCount} deferred</span>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Health tab */}
      {activeTab === 'health' && (
        <SequenceHealth campaignSlug={campaignSlug} />
      )}

      {/* Activity tab */}
      {activeTab === 'activity' && (
        <ActivityFeed campaignSlug={campaignSlug} />
      )}
    </div>
  );
}
