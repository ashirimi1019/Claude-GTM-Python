'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  BarChart3,
  Users,
  Shield,
  Zap,
  Database,
  Radio,
} from 'lucide-react';
import type { IcpPreviewResult, PreviewSource, PreviewStatus } from './types';

// ─── Props ───────────────────────────────────────────

interface PreviewPanelProps {
  result: IcpPreviewResult | null;
  status: PreviewStatus;
  error: string | null;
  onQuickPreview: () => void;
  onLivePreview: () => void;
  disabled: boolean;
}

// ─── Source Badge ────────────────────────────────────

function SourceBadge({ source }: { source: PreviewSource }) {
  const config = {
    db: { label: 'DB Cached', icon: Database, cls: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
    live: { label: 'Live Apollo', icon: Radio, cls: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
    inline: { label: 'Inline', icon: Zap, cls: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  }[source];

  const Icon = config.icon;
  return (
    <span className={cn('inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border', config.cls)}>
      <Icon className="w-2.5 h-2.5" />
      {config.label}
    </span>
  );
}

// ─── Qualification Rate Gauge ───────────────────────

function QualRateGauge({ rate, qualified, total }: { rate: number; qualified: number; total: number }) {
  const pct = Math.round(rate * 100);
  const color =
    pct >= 40 ? 'bg-emerald-500' : pct >= 15 ? 'bg-amber-500' : pct >= 5 ? 'bg-orange-500' : 'bg-red-500';
  const textColor =
    pct >= 40
      ? 'text-emerald-400'
      : pct >= 15
        ? 'text-amber-400'
        : pct >= 5
          ? 'text-orange-400'
          : 'text-red-400';

  return (
    <div className="space-y-1.5">
      <div className="flex items-end justify-between">
        <span className={cn('text-2xl font-bold tabular-nums', textColor)}>{pct}%</span>
        <span className="text-xs text-neutral-500">
          {qualified}/{total} companies
        </span>
      </div>
      <div className="w-full h-2 bg-neutral-800 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500', color)}
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>
      <p className="text-[10px] text-neutral-600">
        {pct >= 40
          ? 'Healthy — broad enough to find good leads'
          : pct >= 15
            ? 'Moderate — may need to relax some filters'
            : pct >= 5
              ? 'Tight — consider broadening criteria'
              : 'Very restrictive — few companies will qualify'}
      </p>
    </div>
  );
}

// ─── Tier Distribution Bar ──────────────────────────

function TierBar({ dist }: { dist: { A: number; B: number; C: number } }) {
  const total = dist.A + dist.B + dist.C;
  if (total === 0) return <p className="text-xs text-neutral-600">No qualified companies</p>;

  const pctA = Math.round((dist.A / total) * 100);
  const pctB = Math.round((dist.B / total) * 100);
  const pctC = 100 - pctA - pctB;

  return (
    <div className="space-y-1.5">
      <div className="flex h-3 rounded-full overflow-hidden bg-neutral-800">
        {pctA > 0 && (
          <div
            className="bg-emerald-500 transition-all duration-500"
            style={{ width: `${pctA}%` }}
            title={`Tier A: ${dist.A}`}
          />
        )}
        {pctB > 0 && (
          <div
            className="bg-blue-500 transition-all duration-500"
            style={{ width: `${pctB}%` }}
            title={`Tier B: ${dist.B}`}
          />
        )}
        {pctC > 0 && (
          <div
            className="bg-neutral-600 transition-all duration-500"
            style={{ width: `${pctC}%` }}
            title={`Tier C: ${dist.C}`}
          />
        )}
      </div>
      <div className="flex gap-3 text-[10px]">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-neutral-400">A: {dist.A}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <span className="text-neutral-400">B: {dist.B}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-neutral-600" />
          <span className="text-neutral-400">C: {dist.C}</span>
        </span>
      </div>
    </div>
  );
}

// ─── Rejection Reasons ──────────────────────────────

function RejectionReasons({ reasons }: { reasons: Array<{ reason: string; count: number }> }) {
  if (reasons.length === 0) return <p className="text-xs text-neutral-600">No rejections</p>;

  const maxCount = reasons[0]?.count ?? 1;

  return (
    <div className="space-y-1.5">
      {reasons.slice(0, 5).map((r) => (
        <div key={r.reason} className="space-y-0.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-neutral-300 truncate mr-2">{formatReasonLabel(r.reason)}</span>
            <span className="text-neutral-500 tabular-nums shrink-0">{r.count}</span>
          </div>
          <div className="w-full h-1 bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-red-500/60 rounded-full"
              style={{ width: `${Math.round((r.count / maxCount) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function formatReasonLabel(reason: string): string {
  return reason
    .replace('score_below_threshold:', 'Low score: ')
    .replace('low_confidence', 'Low data confidence')
    .replace('company_size', 'Company size')
    .replace('industry_excluded', 'Excluded industry')
    .replace('funding_excluded', 'Excluded funding')
    .replace('competitor', 'Competitor detected')
    .replace(/\+/g, ', ');
}

// ─── Sample Companies ───────────────────────────────

function SampleCompanies({
  traces,
  filter,
}: {
  traces: IcpPreviewResult['sampleTraces'];
  filter: 'qualified' | 'rejected';
}) {
  const filtered =
    filter === 'qualified'
      ? traces.filter((t) => t.outcome === 'qualified')
      : traces.filter((t) => t.outcome !== 'qualified');

  if (filtered.length === 0) {
    return (
      <p className="text-xs text-neutral-600">
        No {filter} companies in sample
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      {filtered.map((t) => (
        <div
          key={t.companyId}
          className={cn(
            'flex items-start gap-2 px-2 py-1.5 rounded-lg border text-xs',
            t.outcome === 'qualified'
              ? 'bg-emerald-500/5 border-emerald-500/20'
              : 'bg-red-500/5 border-red-500/20',
          )}
        >
          {t.outcome === 'qualified' ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
          )}
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <span className="font-medium text-neutral-200 truncate">{t.companyName}</span>
              {t.tier && (
                <span
                  className={cn(
                    'text-[9px] px-1 py-0.5 rounded font-medium',
                    t.tier === 'A'
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : t.tier === 'B'
                        ? 'bg-blue-500/20 text-blue-300'
                        : 'bg-neutral-700 text-neutral-400',
                  )}
                >
                  {t.tier}
                </span>
              )}
            </div>
            <p className="text-[10px] text-neutral-500 mt-0.5 line-clamp-2">{t.summary}</p>
            {t.scoring && (
              <p className="text-[10px] text-neutral-600 mt-0.5">
                Score: {t.scoring.total}/{t.scoring.maxPossible} · Confidence: {Math.round(t.confidence.overall * 100)}%
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Confidence Distribution ────────────────────────

function ConfidenceStats({ stats }: { stats: { mean: number; min: number; max: number } }) {
  const format = (n: number) => `${Math.round(n * 100)}%`;

  return (
    <div className="flex gap-4">
      <div className="text-center">
        <p className="text-lg font-bold tabular-nums text-neutral-200">{format(stats.mean)}</p>
        <p className="text-[10px] text-neutral-500">Mean</p>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium tabular-nums text-neutral-400">{format(stats.min)}</p>
        <p className="text-[10px] text-neutral-500">Min</p>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium tabular-nums text-neutral-400">{format(stats.max)}</p>
        <p className="text-[10px] text-neutral-500">Max</p>
      </div>
    </div>
  );
}

// ─── Collapsible Sub-Section ────────────────────────

function SubSection({
  title,
  icon: Icon,
  defaultOpen = false,
  children,
}: {
  title: string;
  icon: React.ElementType;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-t border-neutral-800 pt-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-1.5 text-xs font-medium text-neutral-400 hover:text-neutral-200 transition-colors"
      >
        <Icon className="w-3 h-3" />
        {title}
        {open ? <ChevronDown className="w-3 h-3 ml-auto" /> : <ChevronRight className="w-3 h-3 ml-auto" />}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  );
}

// ─── Main PreviewPanel ──────────────────────────────

export function PreviewPanel({ result, status, error, onQuickPreview, onLivePreview, disabled }: PreviewPanelProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-neutral-200 flex items-center gap-1.5">
        <BarChart3 className="w-3.5 h-3.5" />
        ICP Preview
      </h3>

      {/* Preview Buttons */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onQuickPreview}
          disabled={disabled || status === 'loading'}
          className={cn(
            'flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            'bg-neutral-800 text-neutral-200 border border-neutral-700',
            'hover:bg-neutral-700 hover:text-white',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          {status === 'loading' ? (
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border-2 border-neutral-500 border-t-white rounded-full animate-spin" />
              Running…
            </span>
          ) : (
            <>
              <Database className="w-3 h-3" />
              Quick Preview
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onLivePreview}
          disabled={disabled || status === 'loading'}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            'bg-amber-500/10 text-amber-300 border border-amber-500/30',
            'hover:bg-amber-500/20 hover:text-amber-200',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          )}
          title="Uses 1 Apollo API call (~$0.01)"
        >
          <Radio className="w-3 h-3" />
          Live
        </button>
      </div>

      {/* Help text */}
      {status === 'idle' && !result && (
        <p className="text-[10px] text-neutral-600">
          Preview how your ICP profile performs against sample companies.
          Quick uses cached DB data (free). Live queries Apollo (~$0.01).
        </p>
      )}

      {/* Error state */}
      {status === 'error' && error && (
        <div className="flex items-start gap-1.5 text-[10px] text-red-400 bg-red-500/5 border border-red-500/20 rounded px-2 py-1.5">
          <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {result && status === 'success' && (
        <div className="space-y-3">
          {/* Source + meta */}
          <div className="flex items-center gap-2">
            {result._meta && <SourceBadge source={result._meta.source} />}
            <span className="text-[10px] text-neutral-600">
              {result._meta?.companiesEvaluated ?? result.summary.totalCompanies} companies evaluated
            </span>
          </div>

          {/* Qualification Rate */}
          <QualRateGauge
            rate={result.summary.qualificationRate}
            qualified={result.summary.qualified}
            total={result.summary.totalCompanies}
          />

          {/* Two-Stage Pipeline Banner */}
          {result.twoStageInfo && (
            <div className="text-[10px] text-blue-300/90 bg-blue-500/5 border border-blue-500/15 rounded px-2.5 py-1.5 space-y-1">
              <p className="font-medium">⚡ Two-Stage Pipeline Active</p>
              <p>
                This preview shows <strong>Stage 1 (broad screening)</strong> only.
                {result.twoStageInfo.stage1Shortlisted > 0 && (
                  <> {result.twoStageInfo.stage1Shortlisted} companies shortlisted for enrichment.</>
                )}
              </p>
              <p className="text-blue-400/60">
                Actual runs will enrich shortlisted companies via Apollo and re-score at
                your selected strictness (<strong>{result.effectiveConfig.strictnessLevel.replace('_', ' ')}</strong>).
                Final qualification rate will differ from this preview.
              </p>
            </div>
          )}

          {/* Data-stage guidance when qual is very low on non-broad and no two-stage info */}
          {!result.twoStageInfo &&
            Math.round(result.summary.qualificationRate * 100) < 5 &&
            result.effectiveConfig.strictnessLevel &&
            result.effectiveConfig.strictnessLevel !== 'broad' && (
              <p className="text-[10px] text-amber-400/80 bg-amber-500/5 border border-amber-500/15 rounded px-2.5 py-1.5">
                Tip: Apollo search returns sparse company data. Try <strong>Broad</strong> for initial
                lead discovery, then apply{' '}
                <strong>{result.effectiveConfig.strictnessLevel.replace('_', ' ')}</strong> after
                company enrichment when funding, tech stack, and industry data are populated.
              </p>
            )}

          {/* Tier Distribution */}
          <SubSection title="Tier Distribution" icon={Users} defaultOpen>
            <TierBar dist={result.tierDistribution} />
          </SubSection>

          {/* Top Rejection Reasons */}
          <SubSection title="Top Rejection Reasons" icon={XCircle} defaultOpen>
            <div className="space-y-2">
              <div className="flex flex-wrap gap-3 text-[10px] text-neutral-500">
                <span>Hard filter: {result.rejectionBreakdown['hard-filter']}</span>
                <span>Confidence: {result.rejectionBreakdown.confidence}</span>
                <span>Scoring: {result.rejectionBreakdown.scoring}</span>
                {(result.rejectionBreakdown['after-enrichment'] ?? 0) > 0 && (
                  <span className="text-orange-400">After enrichment: {result.rejectionBreakdown['after-enrichment']}</span>
                )}
              </div>
              <RejectionReasons reasons={result.topRejectionReasons} />
            </div>
          </SubSection>

          {/* Confidence */}
          <SubSection title="Confidence Distribution" icon={Shield}>
            <ConfidenceStats stats={result.confidenceStats} />
          </SubSection>

          {/* Sample Qualified */}
          <SubSection title="Sample Qualified" icon={CheckCircle2}>
            <SampleCompanies traces={result.sampleTraces} filter="qualified" />
          </SubSection>

          {/* Sample Rejected */}
          <SubSection title="Sample Rejected" icon={XCircle}>
            <SampleCompanies traces={result.sampleTraces} filter="rejected" />
          </SubSection>

          {/* Effective Config (collapsed) */}
          <SubSection title="Effective Config" icon={Zap}>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <span className="text-neutral-500">Threshold</span>
              <span className="text-neutral-300 tabular-nums">{result.effectiveConfig.threshold}</span>
              <span className="text-neutral-500">Strictness</span>
              <span className="text-neutral-300">{result.effectiveConfig.strictnessLevel}</span>
              <span className="text-neutral-500">Max score</span>
              <span className="text-neutral-300 tabular-nums">{result.effectiveConfig.maxScore}</span>
              <span className="text-neutral-500">Hiring signal</span>
              <span className="text-neutral-300 tabular-nums">{result.effectiveConfig.hiringSignalMax} pts</span>
            </div>
          </SubSection>
        </div>
      )}
    </div>
  );
}
