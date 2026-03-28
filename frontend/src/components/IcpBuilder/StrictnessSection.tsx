'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight } from 'lucide-react';
import type { IcpStrictnessConfig, StrictnessLevel, IcpExpertOverrides } from './types';
import { Section, NumberInput } from './shared';

interface StrictnessSectionProps {
  value: IcpStrictnessConfig;
  onChange: (value: IcpStrictnessConfig) => void;
  mode: 'quick' | 'advanced';
}

const LEVELS: { value: StrictnessLevel; label: string; badge?: string }[] = [
  { value: 'broad', label: 'Broad' },
  { value: 'balanced', label: 'Balanced', badge: 'Default' },
  { value: 'strict', label: 'Strict' },
  { value: 'very_strict', label: 'Very Strict' },
];

const LEVEL_IMPACTS: Record<StrictnessLevel, string[]> = {
  broad: [
    'Best for Apollo search-level data (sparse company records)',
    'Accepts companies with incomplete data',
    'Lower scoring threshold — tolerates missing fields',
    'Industry/funding preferences are bonuses, not requirements',
  ],
  balanced: [
    'Best when richer company data is available (enriched records)',
    'Standard scoring threshold',
    'Prefers complete data — may reject sparse Apollo search results',
    'Industry/funding preferences boost score',
  ],
  strict: [
    'Requires enriched company data to be effective',
    'Higher scoring threshold',
    'Preferred industries and funding stages become required',
    'Missing tech data is penalized',
  ],
  very_strict: [
    'Requires fully enriched company data',
    'Maximum scoring threshold',
    'All preferred criteria become hard requirements',
    'Missing data fields trigger rejection',
    'Only high-confidence matches pass',
  ],
};

const DEFAULT_OVERRIDES: IcpExpertOverrides = {
  threshold: null,
  dataQuality: null,
  requirePreferredFunding: null,
  requirePreferredIndustries: null,
  rejectMissingTech: null,
  rejectMissingRevenue: null,
  maxCriticalUnknowns: null,
};

export function StrictnessSection({ value, onChange, mode }: StrictnessSectionProps) {
  const [showExpert, setShowExpert] = useState(false);

  const handleLevelChange = (level: StrictnessLevel) => {
    onChange({ ...value, level });
  };

  const handleOverrideChange = (partial: Partial<IcpExpertOverrides>) => {
    const current = value.expertOverrides ?? { ...DEFAULT_OVERRIDES };
    onChange({ ...value, expertOverrides: { ...current, ...partial } });
  };

  return (
    <Section title="Strictness" defaultOpen={false}>
      {/* Level selector */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Strictness Level</span>
        <div className="grid grid-cols-4 gap-1.5">
          {LEVELS.map((lvl) => (
            <button
              key={lvl.value}
              type="button"
              onClick={() => handleLevelChange(lvl.value)}
              className={cn(
                'relative px-3 py-2 rounded-lg border text-xs font-medium text-center transition-colors',
                value.level === lvl.value
                  ? 'bg-indigo-500/10 border-indigo-500/40 text-indigo-300'
                  : 'bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
              )}
            >
              {lvl.label}
              {lvl.badge && (
                <span className="absolute -top-1.5 right-1 text-[8px] px-1 py-0 rounded bg-neutral-700 text-neutral-400">
                  {lvl.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Impact summary */}
      <div className="space-y-1">
        <span className="text-[10px] text-neutral-500 font-medium">
          Impact at {value.level.replace('_', ' ')}:
        </span>
        <ul className="space-y-0.5">
          {LEVEL_IMPACTS[value.level].map((impact, i) => (
            <li key={i} className="text-[10px] text-neutral-400 flex items-start gap-1">
              <span className="text-neutral-600 mt-0.5">-</span>
              {impact}
            </li>
          ))}
        </ul>
      </div>

      {/* Data-stage guidance */}
      {value.level !== 'broad' && (
        <div className="text-[10px] text-amber-400/80 bg-amber-500/5 border border-amber-500/15 rounded px-2.5 py-1.5">
          Apollo search returns sparse company data. Use <strong>Broad</strong> for initial lead discovery.
          {' '}{value.level === 'balanced' ? 'Balanced' : value.level === 'strict' ? 'Strict' : 'Very Strict'}{' '}
          works best after company enrichment, when funding, tech stack, and industry data are populated.
        </div>
      )}

      {/* Advanced: Expert Controls */}
      {mode === 'advanced' && (
        <div className="border border-neutral-800 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setShowExpert(!showExpert)}
            className="w-full flex items-center gap-2 px-3 py-2 text-[10px] font-semibold text-neutral-500 bg-neutral-900/50 hover:bg-neutral-900 transition-colors"
          >
            {showExpert ? (
              <ChevronDown className="w-3 h-3" />
            ) : (
              <ChevronRight className="w-3 h-3" />
            )}
            Expert Controls
          </button>
          {showExpert && (
            <div className="px-3 py-3 space-y-3 bg-neutral-950/50">
              <NumberInput
                label="Custom Threshold Override"
                value={value.expertOverrides?.threshold}
                onChange={(v) => handleOverrideChange({ threshold: v ?? null })}
                placeholder="Use level default"
                min={0}
                helpText="Override the scoring threshold for this strictness level"
              />
              <div className="space-y-1">
                <label className="text-xs font-medium text-neutral-400">Data Quality</label>
                <select
                  value={value.expertOverrides?.dataQuality ?? ''}
                  onChange={(e) =>
                    handleOverrideChange({
                      dataQuality: (e.target.value || null) as IcpExpertOverrides['dataQuality'],
                    })
                  }
                  className={cn(
                    'w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-white',
                    'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
                  )}
                >
                  <option value="">Use level default</option>
                  <option value="accept-incomplete">Accept Incomplete</option>
                  <option value="prefer-complete">Prefer Complete</option>
                  <option value="require-complete">Require Complete</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value.expertOverrides?.requirePreferredFunding ?? false}
                    onChange={(e) =>
                      handleOverrideChange({ requirePreferredFunding: e.target.checked || null })
                    }
                    className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-neutral-300">Require preferred funding stages</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value.expertOverrides?.requirePreferredIndustries ?? false}
                    onChange={(e) =>
                      handleOverrideChange({ requirePreferredIndustries: e.target.checked || null })
                    }
                    className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-neutral-300">Require preferred industries</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value.expertOverrides?.rejectMissingTech ?? false}
                    onChange={(e) =>
                      handleOverrideChange({ rejectMissingTech: e.target.checked || null })
                    }
                    className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-neutral-300">Reject companies with missing tech data</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={value.expertOverrides?.rejectMissingRevenue ?? false}
                    onChange={(e) =>
                      handleOverrideChange({ rejectMissingRevenue: e.target.checked || null })
                    }
                    className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-neutral-300">Reject companies with missing revenue</span>
                </label>
              </div>
              <NumberInput
                label="Max Critical Unknowns"
                value={value.expertOverrides?.maxCriticalUnknowns}
                onChange={(v) => handleOverrideChange({ maxCriticalUnknowns: v ?? null })}
                placeholder="Use level default"
                min={0}
                helpText="Maximum number of unknown critical fields before rejection"
              />
            </div>
          )}
        </div>
      )}
    </Section>
  );
}
