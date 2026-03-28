'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { IcpFundingConfig, IcpRevenueConfig, StrictnessLevel } from './types';
import { FUNDING_STAGES, REVENUE_OPTIONS } from './constants';
import { Section } from './shared';

interface FundingRevenueSectionProps {
  fundingValue: IcpFundingConfig;
  revenueValue: IcpRevenueConfig;
  onFundingChange: (value: IcpFundingConfig) => void;
  onRevenueChange: (value: IcpRevenueConfig) => void;
  mode: 'quick' | 'advanced';
  strictnessLevel: StrictnessLevel;
}

type FundingState = 'neutral' | 'preferred' | 'excluded';

function getFundingState(stage: string, funding: IcpFundingConfig): FundingState {
  if (funding.preferred.includes(stage)) return 'preferred';
  if (funding.excluded.includes(stage)) return 'excluded';
  return 'neutral';
}

function cycleFundingState(stage: string, funding: IcpFundingConfig): IcpFundingConfig {
  const state = getFundingState(stage, funding);
  if (state === 'neutral') {
    return { ...funding, preferred: [...funding.preferred, stage] };
  } else if (state === 'preferred') {
    return {
      ...funding,
      preferred: funding.preferred.filter((s) => s !== stage),
      excluded: [...funding.excluded, stage],
    };
  } else {
    return { ...funding, excluded: funding.excluded.filter((s) => s !== stage) };
  }
}

export function FundingRevenueSection({
  fundingValue,
  revenueValue,
  onFundingChange,
  onRevenueChange,
  mode,
  strictnessLevel,
}: FundingRevenueSectionProps) {
  return (
    <Section title="Funding & Revenue" defaultOpen={true}>
      {/* Funding stages */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">
          Funding Stage — click to cycle: neutral → preferred → excluded
        </span>
        <div className="flex flex-wrap gap-1.5">
          {FUNDING_STAGES.map((stage) => {
            const state = getFundingState(stage.value, fundingValue);
            return (
              <button
                key={stage.value}
                type="button"
                onClick={() => onFundingChange(cycleFundingState(stage.value, fundingValue))}
                className={cn(
                  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
                  state === 'preferred' && 'bg-indigo-500/15 border-indigo-500/40 text-indigo-300',
                  state === 'excluded' && 'bg-red-500/15 border-red-500/40 text-red-300',
                  state === 'neutral' && 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
                )}
                aria-pressed={state !== 'neutral'}
              >
                {stage.label}
              </button>
            );
          })}
        </div>
        <p className="text-[10px] text-neutral-600">
          Stages not in either list receive partial credit (50%).
        </p>
      </div>

      {/* Advanced: acceptable stages */}
      {mode === 'advanced' && (
        <div className="space-y-1.5">
          <span className="text-xs font-medium text-neutral-400">Acceptable Stages (75% credit)</span>
          <div className="flex flex-wrap gap-1.5">
            {FUNDING_STAGES.map((stage) => {
              const state = getFundingState(stage.value, fundingValue);
              if (state !== 'neutral') return null;
              const isAcceptable = fundingValue.acceptable?.includes(stage.value) ?? false;
              return (
                <button
                  key={stage.value}
                  type="button"
                  onClick={() => {
                    const current = fundingValue.acceptable ?? [];
                    const next = isAcceptable
                      ? current.filter((s) => s !== stage.value)
                      : [...current, stage.value];
                    onFundingChange({ ...fundingValue, acceptable: next.length > 0 ? next : null });
                  }}
                  className={cn(
                    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border cursor-pointer select-none transition-colors',
                    isAcceptable
                      ? 'bg-blue-500/15 border-blue-500/40 text-blue-300'
                      : 'bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-600 hover:text-neutral-300',
                  )}
                >
                  {stage.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Revenue */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-neutral-400">Minimum Revenue</label>
        <select
          value={revenueValue.minimum}
          onChange={(e) => onRevenueChange({ ...revenueValue, minimum: Number(e.target.value) })}
          className={cn(
            'w-full bg-neutral-900 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white',
            'focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500',
          )}
        >
          {REVENUE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 cursor-pointer mt-2">
          <input
            type="checkbox"
            checked={revenueValue.inferFromEmployees}
            onChange={(e) => onRevenueChange({ ...revenueValue, inferFromEmployees: e.target.checked })}
            className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-xs text-neutral-300">Infer revenue from employee count when missing</span>
        </label>
      </div>
    </Section>
  );
}
