'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { IcpHiringSignalConfig } from './types';
import { Section } from './shared';

interface SignalsSectionProps {
  value: IcpHiringSignalConfig;
  onChange: (value: IcpHiringSignalConfig) => void;
  mode: 'quick' | 'advanced';
}

const SIGNAL_OPTIONS: { value: IcpHiringSignalConfig['requirement']; label: string; description: string; badge?: string }[] = [
  {
    value: 'required',
    label: 'Required',
    description: 'Only companies with active hiring signals qualify.',
    badge: 'Recommended',
  },
  {
    value: 'preferred',
    label: 'Preferred',
    description: 'Hiring signals boost score, but are not required.',
  },
  {
    value: 'ignored',
    label: 'Ignored',
    description: 'Hiring signals are not considered during scoring.',
  },
];

export function SignalsSection({ value, onChange, mode }: SignalsSectionProps) {
  const handleRequirementChange = (requirement: IcpHiringSignalConfig['requirement']) => {
    onChange({ ...value, requirement });
  };

  return (
    <Section title="Hiring Signals" defaultOpen={false}>
      {/* Radio cards */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Signal Requirement</span>
        <div className="grid grid-cols-1 gap-2">
          {SIGNAL_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleRequirementChange(opt.value)}
              className={cn(
                'w-full text-left px-3 py-2.5 rounded-lg border transition-colors',
                value.requirement === opt.value
                  ? 'bg-indigo-500/10 border-indigo-500/40'
                  : 'bg-neutral-900 border-neutral-700 hover:border-neutral-600',
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'text-xs font-medium',
                    value.requirement === opt.value ? 'text-indigo-300' : 'text-neutral-300',
                  )}
                >
                  {opt.label}
                </span>
                {opt.badge && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-900/50 text-indigo-300 border border-indigo-700/50">
                    {opt.badge}
                  </span>
                )}
              </div>
              <p className="text-[10px] text-neutral-500 mt-0.5">{opt.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Advanced: weight sliders */}
      {mode === 'advanced' && value.requirement !== 'ignored' && (
        <div className="space-y-2">
          <span className="text-xs font-medium text-neutral-400">Quality Weights (must sum to 1.0)</span>
          <div className="space-y-2">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[10px] text-neutral-500">Freshness Weight</label>
                <span className="text-[10px] text-neutral-400">
                  {(value.qualityWeights?.freshnessWeight ?? 0.6).toFixed(1)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={value.qualityWeights?.freshnessWeight ?? 0.6}
                onChange={(e) => {
                  const freshness = parseFloat(e.target.value);
                  const intensity = Math.round((1 - freshness) * 10) / 10;
                  onChange({
                    ...value,
                    qualityWeights: { freshnessWeight: freshness, intensityWeight: intensity },
                  });
                }}
                className="w-full accent-indigo-500"
              />
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[10px] text-neutral-500">Intensity Weight</label>
                <span className="text-[10px] text-neutral-400">
                  {(value.qualityWeights?.intensityWeight ?? 0.4).toFixed(1)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={1}
                step={0.1}
                value={value.qualityWeights?.intensityWeight ?? 0.4}
                onChange={(e) => {
                  const intensity = parseFloat(e.target.value);
                  const freshness = Math.round((1 - intensity) * 10) / 10;
                  onChange({
                    ...value,
                    qualityWeights: { freshnessWeight: freshness, intensityWeight: intensity },
                  });
                }}
                className="w-full accent-indigo-500"
              />
            </div>
          </div>
        </div>
      )}
    </Section>
  );
}
