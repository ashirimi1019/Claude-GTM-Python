'use client';

import React from 'react';
import {
  Search,
  Filter,
  Database,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  TrendingDown,
  ArrowRight,
} from 'lucide-react';

// ─── Types (mirrors TwoStageRunSummary from backend) ─────

export interface RunSummaryData {
  schemaVersion: number;
  summaryType: string;
  generatedAt: string;
  runStartedAt: string;
  offerSlug: string;
  campaignSlug: string;
  selectedStrictness: string;
  totalSearchCandidates: number;
  stage1Shortlisted: number;
  stage1QualRate: number;
  enrichAttempted: number;
  enrichSucceeded: number;
  enrichRate: number;
  enrichCreditsEstimate: number;
  enrichDurationMs: number;
  stage2Qualified: number;
  rejectedAfterEnrichment: number;
  finalQualRate: number;
  pipelineDurationMs: number;
  outcomeBreakdown: Record<string, number>;
  stage2RejectionReasons: Record<string, number>;
}

// ─── Helpers ─────────────────────────────────────────

function pct(n: number): string {
  return `${n}%`;
}

function dur(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

function fmtStrictness(s: string): string {
  return s.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

// ─── Funnel Step ─────────────────────────────────────

function FunnelStep({
  icon: Icon,
  label,
  value,
  sub,
  highlight,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  highlight?: 'green' | 'amber' | 'red' | 'neutral';
}) {
  const color = {
    green: 'text-emerald-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
    neutral: 'text-neutral-300',
  }[highlight ?? 'neutral'];

  return (
    <div className="flex items-center gap-2 py-1.5">
      <Icon className="w-3.5 h-3.5 text-neutral-500 shrink-0" />
      <div className="flex-1 min-w-0">
        <span className="text-[11px] text-neutral-400">{label}</span>
      </div>
      <div className="text-right shrink-0">
        <span className={`text-sm font-semibold tabular-nums ${color}`}>{value}</span>
        {sub && <span className="text-[10px] text-neutral-500 ml-1">{sub}</span>}
      </div>
    </div>
  );
}

// ─── Warning Banner ──────────────────────────────────

function WarningBanner({ icon: Icon, message }: { icon: React.ElementType; message: string }) {
  return (
    <div className="flex items-start gap-1.5 text-[10px] text-amber-400/90 bg-amber-500/5 border border-amber-500/20 rounded px-2.5 py-1.5">
      <Icon className="w-3 h-3 shrink-0 mt-0.5" />
      <span>{message}</span>
    </div>
  );
}

// ─── Checklist Item ─────────────────────────────────

function ChecklistItem({ ok, label, warn }: { ok: boolean; label: string; warn?: string }) {
  return (
    <div className="flex items-start gap-1.5">
      <span className={ok ? 'text-emerald-500' : 'text-amber-400'}>
        {ok ? '☑' : '⚠'}
      </span>
      <div>
        <span className="text-neutral-400">{label}</span>
        {warn && <span className="text-amber-400/70 ml-1">— {warn}</span>}
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────

interface RunSummaryCardProps {
  summary: RunSummaryData;
}

export function RunSummaryCard({ summary }: RunSummaryCardProps) {
  const s = summary;

  // Derived metrics
  const rejectRatio =
    s.stage1Shortlisted > 0 ? Math.round((s.rejectedAfterEnrichment / s.stage1Shortlisted) * 100) : 0;

  // Warning thresholds
  const lowEnrichment = s.enrichRate < 50;
  const highRejectRate = rejectRatio > 80;

  const finalRateColor: 'green' | 'amber' | 'red' =
    s.finalQualRate >= 15 ? 'green' : s.finalQualRate >= 5 ? 'amber' : 'red';
  const enrichRateColor: 'green' | 'amber' | 'red' =
    s.enrichRate >= 70 ? 'green' : s.enrichRate >= 40 ? 'amber' : 'red';

  return (
    <div className="bg-neutral-900/60 border border-neutral-800 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <h3 className="text-xs font-semibold text-neutral-200">
            Two-Stage Pipeline Results
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-neutral-500">
          <span>{fmtStrictness(s.selectedStrictness)}</span>
          <span>·</span>
          <span>{timeAgo(s.generatedAt)}</span>
        </div>
      </div>

      {/* Warnings */}
      {lowEnrichment && (
        <WarningBanner
          icon={TrendingDown}
          message={`Low enrichment rate (${pct(s.enrichRate)}). Apollo may have limited data for companies in this ICP. Stage 2 ran on sparse data for ${s.enrichAttempted - s.enrichSucceeded} companies.`}
        />
      )}
      {highRejectRate && (
        <WarningBanner
          icon={AlertTriangle}
          message={`${rejectRatio}% of shortlisted companies were rejected after enrichment. Consider whether ${fmtStrictness(s.selectedStrictness)} strictness is too narrow for this ICP.`}
        />
      )}

      {/* Funnel */}
      <div className="space-y-0.5">
        <FunnelStep
          icon={Search}
          label="Search candidates"
          value={s.totalSearchCandidates}
          highlight="neutral"
        />

        <div className="flex items-center gap-1 pl-5">
          <ArrowRight className="w-2.5 h-2.5 text-neutral-600" />
          <span className="text-[9px] text-neutral-600 uppercase tracking-wider">Stage 1 · Broad screen</span>
        </div>

        <FunnelStep
          icon={Filter}
          label="Shortlisted"
          value={s.stage1Shortlisted}
          sub={pct(s.stage1QualRate)}
          highlight="neutral"
        />

        <div className="flex items-center gap-1 pl-5">
          <ArrowRight className="w-2.5 h-2.5 text-neutral-600" />
          <span className="text-[9px] text-neutral-600 uppercase tracking-wider">Enrichment</span>
        </div>

        <FunnelStep
          icon={Database}
          label="Enriched"
          value={`${s.enrichSucceeded}/${s.enrichAttempted}`}
          sub={pct(s.enrichRate)}
          highlight={enrichRateColor}
        />

        <div className="flex items-center gap-1 pl-5">
          <ArrowRight className="w-2.5 h-2.5 text-neutral-600" />
          <span className="text-[9px] text-neutral-600 uppercase tracking-wider">Stage 2 · {fmtStrictness(s.selectedStrictness)}</span>
        </div>

        <FunnelStep
          icon={CheckCircle2}
          label="Qualified"
          value={s.stage2Qualified}
          sub={`${pct(s.finalQualRate)} final`}
          highlight={finalRateColor}
        />

        {s.rejectedAfterEnrichment > 0 && (
          <FunnelStep
            icon={XCircle}
            label="Rejected after enrichment"
            value={s.rejectedAfterEnrichment}
            highlight="red"
          />
        )}
      </div>

      {/* Timing + cost row */}
      <div className="flex items-center justify-between border-t border-neutral-800 pt-2">
        <div className="flex items-center gap-3 text-[10px] text-neutral-500">
          <span className="flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" />
            {dur(s.pipelineDurationMs)} total
          </span>
          <span>
            Enrich: {dur(s.enrichDurationMs)}
          </span>
        </div>
        <span className="text-[10px] text-neutral-500">
          ~{s.enrichCreditsEstimate} Apollo credits
        </span>
      </div>

      {/* Stage 2 rejection breakdown */}
      {Object.keys(s.stage2RejectionReasons).length > 0 && (
        <div className="border-t border-neutral-800 pt-2">
          <span className="text-[10px] text-neutral-500 font-medium">Stage 2 rejections</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(s.stage2RejectionReasons)
              .sort(([, a], [, b]) => b - a)
              .map(([reason, count]) => (
                <span
                  key={reason}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400/80 border border-red-500/15"
                >
                  {reason.replace('rejected-', '')}: {count}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Baseline collection checklist */}
      <div className="border-t border-neutral-800 pt-2 space-y-1">
        <span className="text-[10px] text-neutral-500 font-medium">Baseline Checklist</span>
        <div className="grid grid-cols-1 gap-0.5 text-[10px]">
          <ChecklistItem ok={true} label={`ICP profile: ${fmtStrictness(s.selectedStrictness)}`} />
          <ChecklistItem ok={s.totalSearchCandidates > 0} label={`Run completed: ${s.totalSearchCandidates} candidates searched`} />
          <ChecklistItem
            ok={s.enrichRate >= 50}
            label={`Enrich rate: ${pct(s.enrichRate)}`}
            warn={s.enrichRate < 50 ? 'Low — Apollo may have limited coverage' : undefined}
          />
          <ChecklistItem
            ok={rejectRatio <= 80}
            label={`Reject-after-enrichment: ${rejectRatio}%`}
            warn={rejectRatio > 80 ? 'High — broad screen may be too permissive' : undefined}
          />
          <ChecklistItem
            ok={s.finalQualRate >= 5}
            label={`Final qual rate: ${pct(s.finalQualRate)}`}
            warn={s.finalQualRate < 5 ? 'Very low — review ICP dimensions' : undefined}
          />
        </div>
        <p className="text-[9px] text-neutral-600 pt-1">
          Collect 5–10 runs, then run <code className="text-neutral-500 bg-neutral-800 px-1 rounded">npm run baseline</code> for aggregate analysis.
        </p>
      </div>

      {/* Actual run label */}
      <div className="text-center">
        <span className="text-[9px] text-neutral-600 uppercase tracking-wider">
          Actual run results · not a preview estimate
        </span>
      </div>
    </div>
  );
}
