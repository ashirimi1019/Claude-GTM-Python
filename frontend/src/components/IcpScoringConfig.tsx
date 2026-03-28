'use client';

import React, { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Plus, X } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types — mirrors ScoringConfigOverrides from scoring.ts
// ---------------------------------------------------------------------------

export interface ScoringConfigOverrides {
  threshold?: number;
  optimalSizeMin?: number;
  optimalSizeMax?: number;
  acceptableSizeMax?: number;
  partialSizeMin?: number;
  minRevenue?: number;
  maxEmployees?: number | null;
  techKeywords?: string[];
  disqualifySectors?: string[];
  preferredFundingStages?: string[];
  excludedFundingStages?: string[];
}

// ---------------------------------------------------------------------------
// Presets — hardcoded vertical defaults (mirrors scoring.md YAML blocks)
// ---------------------------------------------------------------------------

export const VERTICAL_PRESETS: Record<string, { label: string; config: ScoringConfigOverrides }> = {
  staffing: {
    label: 'Staffing (TaaS)',
    config: {
      threshold: 190,
      optimalSizeMin: 100,
      optimalSizeMax: 2000,
      acceptableSizeMax: 5000,
      partialSizeMin: 50,
      minRevenue: 10_000_000,
      techKeywords: [
        'spark', 'airflow', 'dbt', 'snowflake', 'databricks', 'kafka',
        'flink', 'pytorch', 'tensorflow', 'mlflow', 'terraform', 'pulumi',
        'go', 'rust',
      ],
      disqualifySectors: [
        'government', 'academia', 'staffing', 'recruiting', 'nonprofit',
        'religious', 'military', 'political', 'gambling', 'tobacco',
      ],
      preferredFundingStages: ['series_a', 'series_b', 'series_c', 'series_d', 'series_e'],
      excludedFundingStages: ['pre_seed', 'seed'],
    },
  },
  'ai-data-consulting': {
    label: 'AI & Data Consulting',
    config: {
      threshold: 180,
      optimalSizeMin: 200,
      optimalSizeMax: 5000,
      acceptableSizeMax: 10000,
      partialSizeMin: 50,
      minRevenue: 20_000_000,
      techKeywords: [
        'machine learning', 'ai', 'data platform', 'data engineering', 'mlops',
        'databricks', 'snowflake', 'spark', 'dbt', 'airflow', 'llm',
        'generative ai', 'data lake', 'data warehouse', 'vector database',
      ],
      disqualifySectors: [
        'government', 'academia', 'staffing', 'recruiting', 'nonprofit',
      ],
      preferredFundingStages: ['series_b', 'series_c', 'series_d', 'series_e', 'private_equity'],
      excludedFundingStages: ['pre_seed', 'seed'],
    },
  },
  'cloud-software-delivery': {
    label: 'Cloud & Software Delivery',
    config: {
      threshold: 180,
      optimalSizeMin: 100,
      optimalSizeMax: 5000,
      acceptableSizeMax: 10000,
      partialSizeMin: 50,
      minRevenue: 20_000_000,
      techKeywords: [
        'kubernetes', 'docker', 'terraform', 'aws', 'gcp', 'azure',
        'cloud native', 'devops', 'platform engineering', 'sre',
        'microservices', 'ci/cd', 'infrastructure as code',
      ],
      disqualifySectors: [
        'government', 'academia', 'staffing', 'recruiting', 'nonprofit',
        'gambling', 'tobacco',
      ],
      preferredFundingStages: ['series_a', 'series_b', 'series_c', 'series_d'],
      excludedFundingStages: ['pre_seed', 'seed', 'pre-seed'],
    },
  },
  'small-startups': {
    label: 'Small Startups (20-100 employees)',
    config: {
      threshold: 150,
      optimalSizeMin: 20,
      optimalSizeMax: 100,
      acceptableSizeMax: 200,
      partialSizeMin: 10,
      minRevenue: 2_000_000,
      preferredFundingStages: ['seed', 'series_a', 'series_b'],
      excludedFundingStages: [],
    },
  },
  enterprise: {
    label: 'Enterprise (1000+ employees)',
    config: {
      threshold: 170,
      optimalSizeMin: 1000,
      optimalSizeMax: 10000,
      acceptableSizeMax: 50000,
      partialSizeMin: 500,
      minRevenue: 50_000_000,
      preferredFundingStages: ['series_d', 'series_e', 'private_equity', 'ipo', 'public'],
      excludedFundingStages: ['pre_seed', 'seed'],
    },
  },
};

// ---------------------------------------------------------------------------
// Funding stage options
// ---------------------------------------------------------------------------

const FUNDING_STAGES = [
  'pre_seed', 'seed', 'series_a', 'series_b', 'series_c',
  'series_d', 'series_e', 'series_f', 'private_equity', 'ipo', 'public',
];

const FUNDING_STAGE_LABELS: Record<string, string> = {
  pre_seed: 'Pre-Seed',
  seed: 'Seed',
  series_a: 'Series A',
  series_b: 'Series B',
  series_c: 'Series C',
  series_d: 'Series D',
  series_e: 'Series E',
  series_f: 'Series F',
  private_equity: 'Private Equity',
  ipo: 'IPO',
  public: 'Public',
};

// ---------------------------------------------------------------------------
// Common disqualify sector options
// ---------------------------------------------------------------------------

const COMMON_SECTORS = [
  'government', 'academia', 'staffing', 'recruiting', 'nonprofit',
  'religious', 'military', 'political', 'gambling', 'tobacco',
];

// ---------------------------------------------------------------------------
// Pill helper (matches GeographySelect styling)
// ---------------------------------------------------------------------------

const pillCls = (active: boolean) =>
  cn(
    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
    active
      ? 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300'
      : 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
  );

const dangerPillCls = (active: boolean) =>
  cn(
    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
    active
      ? 'bg-red-500/15 border-red-500/40 text-red-300'
      : 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
  );

// ---------------------------------------------------------------------------
// Number input helper
// ---------------------------------------------------------------------------

function NumberInput({
  label,
  value,
  onChange,
  placeholder,
  suffix,
  prefix,
  min,
  helpText,
}: {
  label: string;
  value: number | undefined | null;
  onChange: (v: number | undefined) => void;
  placeholder?: string;
  suffix?: string;
  prefix?: string;
  min?: number;
  helpText?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-medium text-neutral-400">{label}</label>
      <div className="flex items-center gap-1">
        {prefix && <span className="text-xs text-neutral-500">{prefix}</span>}
        <input
          type="number"
          value={value ?? ''}
          onChange={(e) => {
            const raw = e.target.value;
            if (raw === '') {
              onChange(undefined);
            } else {
              const n = parseInt(raw, 10);
              if (!isNaN(n) && (min === undefined || n >= min)) onChange(n);
            }
          }}
          placeholder={placeholder}
          min={min}
          className={cn(
            'w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder:text-neutral-600',
          )}
        />
        {suffix && <span className="text-xs text-neutral-500">{suffix}</span>}
      </div>
      {helpText && <p className="text-[10px] text-neutral-600">{helpText}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tag input (for keywords / sectors)
// ---------------------------------------------------------------------------

function TagInput({
  label,
  tags,
  onChange,
  suggestions,
  placeholder,
  variant = 'default',
}: {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  suggestions?: string[];
  placeholder?: string;
  variant?: 'default' | 'danger';
}) {
  const [inputValue, setInputValue] = useState('');
  const cls = variant === 'danger' ? dangerPillCls : pillCls;

  const addTag = (tag: string) => {
    const cleaned = tag.toLowerCase().trim();
    if (cleaned && !tags.includes(cleaned)) {
      onChange([...tags, cleaned]);
    }
    setInputValue('');
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag(inputValue);
    }
  };

  // Suggestions not yet added
  const available = suggestions?.filter((s) => !tags.includes(s)) ?? [];

  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-neutral-400">{label}</label>
      {/* Current tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => removeTag(tag)}
              className={cls(true)}
            >
              {tag}
              <X className="w-3 h-3" />
            </button>
          ))}
        </div>
      )}
      {/* Input */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Type and press Enter'}
          className={cn(
            'flex-1 bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder:text-neutral-600',
          )}
        />
        <button
          type="button"
          onClick={() => addTag(inputValue)}
          disabled={!inputValue.trim()}
          className="p-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-400 hover:text-white hover:border-neutral-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>
      {/* Quick-add suggestions */}
      {available.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {available.slice(0, 8).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => addTag(s)}
              className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-800/50 border border-neutral-700/50 text-neutral-500 hover:text-neutral-300 hover:border-neutral-600 transition-colors"
            >
              + {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Collapsible section
// ---------------------------------------------------------------------------

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-neutral-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-neutral-300 bg-neutral-900/50 hover:bg-neutral-900 transition-colors"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        {title}
      </button>
      {open && <div className="px-3 py-3 space-y-3 bg-neutral-950/50">{children}</div>}
    </div>
  );
}

// =========================================================================
// IcpScoringConfig (editable form)
// =========================================================================

export interface IcpScoringConfigProps {
  value: ScoringConfigOverrides | null;
  onChange: (value: ScoringConfigOverrides | null) => void;
  showInherit?: boolean;
}

export function IcpScoringConfig({ value, onChange, showInherit = false }: IcpScoringConfigProps) {
  const [mode, setMode] = useState<'inherit' | 'preset' | 'custom'>(
    value === null ? 'inherit' : 'custom',
  );

  const handleModeChange = (newMode: string) => {
    if (newMode === 'inherit') {
      setMode('inherit');
      onChange(null);
    } else if (newMode in VERTICAL_PRESETS) {
      setMode('preset');
      onChange({ ...VERTICAL_PRESETS[newMode].config });
    } else if (newMode === 'custom') {
      setMode('custom');
      // If transitioning from inherit, start with empty overrides
      if (!value) onChange({});
    }
  };

  const update = useCallback(
    (partial: Partial<ScoringConfigOverrides>) => {
      onChange({ ...(value ?? {}), ...partial });
    },
    [value, onChange],
  );

  return (
    <div className="space-y-4">
      {/* Mode selector */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-neutral-400">ICP Scoring Profile</label>
        <select
          value={mode === 'inherit' ? 'inherit' : mode === 'preset' ? 'preset' : 'custom'}
          onChange={(e) => handleModeChange(e.target.value)}
          className={cn(
            'w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
          )}
        >
          <option value="inherit">{showInherit ? 'Inherit from offer' : 'Use vertical defaults'}</option>
          {Object.entries(VERTICAL_PRESETS).map(([key, preset]) => (
            <option key={key} value={key}>
              {preset.label}
            </option>
          ))}
          <option value="custom">Custom configuration</option>
        </select>
      </div>

      {/* Custom / preset editor — show when not inheriting */}
      {mode !== 'inherit' && value && (
        <div className="space-y-3">
          {/* Threshold */}
          <Section title="Qualification Threshold" defaultOpen={true}>
            <NumberInput
              label="Minimum ICP Score"
              value={value.threshold}
              onChange={(v) => update({ threshold: v })}
              placeholder="170"
              min={0}
              helpText="Companies below this score are not enriched (saves Apollo credits). Default: 170"
            />
          </Section>

          {/* Company Size */}
          <Section title="Company Size Bands" defaultOpen={true}>
            <div className="grid grid-cols-2 gap-3">
              <NumberInput
                label="Optimal Min"
                value={value.optimalSizeMin}
                onChange={(v) => update({ optimalSizeMin: v })}
                placeholder="100"
                suffix="employees"
                min={1}
              />
              <NumberInput
                label="Optimal Max"
                value={value.optimalSizeMax}
                onChange={(v) => update({ optimalSizeMax: v })}
                placeholder="2000"
                suffix="employees"
                min={1}
              />
              <NumberInput
                label="Acceptable Max"
                value={value.acceptableSizeMax}
                onChange={(v) => update({ acceptableSizeMax: v })}
                placeholder="5000"
                suffix="employees"
                min={1}
              />
              <NumberInput
                label="Partial Min"
                value={value.partialSizeMin}
                onChange={(v) => update({ partialSizeMin: v })}
                placeholder="50"
                suffix="employees"
                min={1}
              />
            </div>
            <NumberInput
              label="Hard Ceiling (Max Employees)"
              value={value.maxEmployees}
              onChange={(v) => update({ maxEmployees: v ?? null })}
              placeholder="No limit"
              suffix="employees"
              min={1}
              helpText="Companies above this are hard-rejected before scoring. Leave empty for no limit."
            />
            {/* Visual band diagram */}
            {(value.partialSizeMin || value.optimalSizeMin || value.optimalSizeMax || value.acceptableSizeMax) && (
              <div className="mt-2 space-y-1">
                <p className="text-[10px] text-neutral-500 font-medium">Size Band Preview</p>
                <div className="flex items-center gap-0.5 text-[10px]">
                  <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-500">
                    {'<'}{value.partialSizeMin ?? 50} skip
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                    {value.partialSizeMin ?? 50}–{(value.optimalSizeMin ?? 100) - 1} partial
                  </span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                    {value.optimalSizeMin ?? 100}–{value.optimalSizeMax ?? 2000} optimal
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400">
                    {(value.optimalSizeMax ?? 2000) + 1}–{value.acceptableSizeMax ?? 5000} acceptable
                  </span>
                  <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-500">
                    {'>'}{value.acceptableSizeMax ?? 5000} skip
                  </span>
                </div>
              </div>
            )}
          </Section>

          {/* Revenue */}
          <Section title="Revenue Threshold" defaultOpen={false}>
            <NumberInput
              label="Minimum Annual Revenue"
              value={value.minRevenue}
              onChange={(v) => update({ minRevenue: v })}
              placeholder="10000000"
              prefix="$"
              min={0}
              helpText={`Currently: $${((value.minRevenue ?? 10_000_000) / 1_000_000).toFixed(0)}M`}
            />
          </Section>

          {/* Tech Keywords */}
          <Section title="Tech Keywords" defaultOpen={false}>
            <TagInput
              label="Companies matching these keywords get bonus points"
              tags={value.techKeywords ?? []}
              onChange={(tags) => update({ techKeywords: tags })}
              suggestions={[
                'kubernetes', 'spark', 'airflow', 'dbt', 'snowflake', 'databricks',
                'kafka', 'terraform', 'docker', 'aws', 'gcp', 'azure', 'pytorch',
                'tensorflow', 'mlflow', 'go', 'rust', 'microservices',
              ]}
              placeholder="Add tech keyword..."
            />
          </Section>

          {/* Sector Exclusions */}
          <Section title="Sector Exclusions" defaultOpen={false}>
            <TagInput
              label="Companies in these sectors are hard-rejected"
              tags={value.disqualifySectors ?? []}
              onChange={(tags) => update({ disqualifySectors: tags })}
              suggestions={COMMON_SECTORS}
              placeholder="Add sector..."
              variant="danger"
            />
          </Section>

          {/* Funding Stages */}
          <Section title="Funding Stage Preferences" defaultOpen={false}>
            <div className="space-y-3">
              <div>
                <span className="text-xs font-medium text-neutral-400">Preferred Stages (full credit)</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {FUNDING_STAGES.map((stage) => {
                    const active = (value.preferredFundingStages ?? []).includes(stage);
                    const excluded = (value.excludedFundingStages ?? []).includes(stage);
                    return (
                      <button
                        key={stage}
                        type="button"
                        disabled={excluded}
                        onClick={() => {
                          const current = value.preferredFundingStages ?? [];
                          if (active) {
                            update({ preferredFundingStages: current.filter((s) => s !== stage) });
                          } else {
                            update({ preferredFundingStages: [...current, stage] });
                          }
                        }}
                        className={cn(pillCls(active), excluded && 'opacity-30 cursor-not-allowed')}
                        aria-pressed={active}
                      >
                        {FUNDING_STAGE_LABELS[stage] ?? stage}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <span className="text-xs font-medium text-neutral-400">Excluded Stages (hard reject)</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {FUNDING_STAGES.map((stage) => {
                    const active = (value.excludedFundingStages ?? []).includes(stage);
                    const preferred = (value.preferredFundingStages ?? []).includes(stage);
                    return (
                      <button
                        key={stage}
                        type="button"
                        disabled={preferred}
                        onClick={() => {
                          const current = value.excludedFundingStages ?? [];
                          if (active) {
                            update({ excludedFundingStages: current.filter((s) => s !== stage) });
                          } else {
                            update({ excludedFundingStages: [...current, stage] });
                          }
                        }}
                        className={cn(dangerPillCls(active), preferred && 'opacity-30 cursor-not-allowed')}
                        aria-pressed={active}
                      >
                        {FUNDING_STAGE_LABELS[stage] ?? stage}
                      </button>
                    );
                  })}
                </div>
                <p className="text-[10px] text-neutral-600 mt-1">
                  Stages not in either list receive partial credit (50%).
                </p>
              </div>
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}

// =========================================================================
// IcpScoringDisplay (read-only, for Pipeline tab)
// =========================================================================

export interface IcpScoringDisplayProps {
  config: ScoringConfigOverrides | null;
  source: 'campaign' | 'offer' | 'vertical';
}

export function IcpScoringDisplay({ config, source }: IcpScoringDisplayProps) {
  const sourceLabel =
    source === 'campaign'
      ? '(campaign override)'
      : source === 'offer'
        ? '(from offer)'
        : '(vertical default)';

  const sourceColor =
    source === 'campaign'
      ? 'text-indigo-400/60'
      : source === 'offer'
        ? 'text-violet-400/60'
        : 'text-neutral-500';

  if (!config) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500">Using vertical defaults</span>
        <span className={`text-[10px] ${sourceColor}`}>{sourceLabel}</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] ${sourceColor}`}>{sourceLabel}</span>
      </div>
      {/* Key metrics as inline pills */}
      <div className="flex flex-wrap gap-2">
        {config.threshold !== undefined && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-800 border border-neutral-700 text-neutral-300">
            Threshold: {config.threshold}
          </span>
        )}
        {(config.optimalSizeMin !== undefined || config.optimalSizeMax !== undefined) && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            Size: {config.optimalSizeMin ?? '?'}–{config.optimalSizeMax ?? '?'} optimal
          </span>
        )}
        {config.acceptableSizeMax !== undefined && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400">
            up to {config.acceptableSizeMax} acceptable
          </span>
        )}
        {config.minRevenue !== undefined && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-800 border border-neutral-700 text-neutral-300">
            Rev: ${(config.minRevenue / 1_000_000).toFixed(0)}M+
          </span>
        )}
        {config.maxEmployees !== undefined && config.maxEmployees !== null && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400">
            Max: {config.maxEmployees.toLocaleString()} employees
          </span>
        )}
      </div>
      {/* Tech keywords */}
      {config.techKeywords && config.techKeywords.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-neutral-500">Tech keywords:</span>
          <div className="flex flex-wrap gap-1">
            {config.techKeywords.map((kw) => (
              <span key={kw} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400">
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}
      {/* Excluded sectors */}
      {config.disqualifySectors && config.disqualifySectors.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-neutral-500">Excluded sectors:</span>
          <div className="flex flex-wrap gap-1">
            {config.disqualifySectors.map((s) => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
      {/* Funding stages */}
      {config.preferredFundingStages && config.preferredFundingStages.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-neutral-500">Preferred stages:</span>
          <div className="flex flex-wrap gap-1">
            {config.preferredFundingStages.map((s) => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
                {FUNDING_STAGE_LABELS[s] ?? s}
              </span>
            ))}
          </div>
        </div>
      )}
      {config.excludedFundingStages && config.excludedFundingStages.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-neutral-500">Excluded stages:</span>
          <div className="flex flex-wrap gap-1">
            {config.excludedFundingStages.map((s) => (
              <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400">
                {FUNDING_STAGE_LABELS[s] ?? s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
