'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { IcpCompanySize, SizePreset } from './types';
import { SIZE_PRESET_VALUES } from './constants';
import { PillButton, NumberInput, Section } from './shared';

const SIZE_PRESETS: { value: SizePreset | 'custom'; label: string }[] = [
  { value: 'startup', label: 'Startup' },
  { value: 'smb', label: 'SMB' },
  { value: 'mid-market', label: 'Mid-Market' },
  { value: 'enterprise', label: 'Enterprise' },
  { value: 'any', label: 'Any Size' },
  { value: 'custom', label: 'Custom' },
];

interface SizeSectionProps {
  value: IcpCompanySize;
  onChange: (value: IcpCompanySize) => void;
  mode: 'quick' | 'advanced';
}

export function SizeSection({ value, onChange, mode }: SizeSectionProps) {
  const isCustom = value.preset === null || !SIZE_PRESET_VALUES[value.preset];

  const handlePresetClick = (preset: SizePreset | 'custom') => {
    if (preset === 'custom') {
      onChange({ ...value, preset: null });
      return;
    }
    const bounds = SIZE_PRESET_VALUES[preset];
    if (bounds) {
      onChange({
        ...value,
        preset,
        hardMin: bounds.hardMin,
        idealMin: bounds.idealMin,
        idealMax: bounds.idealMax,
        hardMax: bounds.hardMax,
      });
    }
  };

  return (
    <Section title="Company Size" defaultOpen={true}>
      {/* Quick mode: preset pills */}
      <div>
        <span className="text-xs font-medium text-neutral-400">Size Range</span>
        <div className="flex flex-wrap gap-1.5 mt-1.5">
          {SIZE_PRESETS.map((p) => (
            <PillButton
              key={p.value}
              active={p.value === 'custom' ? isCustom : value.preset === p.value}
              onClick={() => handlePresetClick(p.value)}
            >
              {p.label}
            </PillButton>
          ))}
        </div>
      </div>

      {/* Advanced mode or custom: show number inputs */}
      {(mode === 'advanced' || isCustom) && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <NumberInput
              label="Hard Min"
              value={value.hardMin}
              onChange={(v) => onChange({ ...value, hardMin: v ?? null, preset: null })}
              placeholder="No minimum"
              suffix="employees"
              min={1}
            />
            <NumberInput
              label="Ideal Min"
              value={value.idealMin}
              onChange={(v) => onChange({ ...value, idealMin: v ?? 1, preset: null })}
              placeholder="100"
              suffix="employees"
              min={1}
            />
            <NumberInput
              label="Ideal Max"
              value={value.idealMax}
              onChange={(v) => onChange({ ...value, idealMax: v ?? 10000, preset: null })}
              placeholder="2000"
              suffix="employees"
              min={1}
            />
            <NumberInput
              label="Hard Max"
              value={value.hardMax}
              onChange={(v) => onChange({ ...value, hardMax: v ?? null, preset: null })}
              placeholder="No limit"
              suffix="employees"
              min={1}
            />
          </div>

          {/* Band preview */}
          <div className="space-y-1">
            <p className="text-[10px] text-neutral-500 font-medium">Size Band Preview</p>
            <div className="flex items-center gap-0.5 text-[10px] flex-wrap">
              {value.hardMin !== null && (
                <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-500">
                  {'<'}{value.hardMin} reject
                </span>
              )}
              <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                {value.hardMin ?? '0'}–{value.idealMin - 1} partial
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                {value.idealMin}–{value.idealMax} optimal
              </span>
              {value.hardMax !== null && (
                <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400">
                  {value.idealMax + 1}–{value.hardMax} acceptable
                </span>
              )}
              {value.hardMax !== null && (
                <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-500">
                  {'>'}{value.hardMax} reject
                </span>
              )}
            </div>
          </div>

          {/* Toggle options */}
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={value.rejectOutsideHardRange}
                onChange={(e) => onChange({ ...value, rejectOutsideHardRange: e.target.checked })}
                className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs text-neutral-300">Reject companies outside hard range</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={value.unknownSizeBehavior === 'reject'}
                onChange={(e) =>
                  onChange({
                    ...value,
                    unknownSizeBehavior: e.target.checked ? 'reject' : 'allow-with-penalty',
                  })
                }
                className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-xs text-neutral-300">Reject companies with unknown size</span>
            </label>
          </div>
        </>
      )}

      {/* Quick mode: show summary */}
      {mode === 'quick' && !isCustom && value.preset && SIZE_PRESET_VALUES[value.preset] && (
        <p className="text-[10px] text-neutral-500">
          {value.idealMin.toLocaleString()}–{value.idealMax.toLocaleString()} ideal
          {value.hardMax ? `, up to ${value.hardMax.toLocaleString()} acceptable` : ''}
        </p>
      )}
    </Section>
  );
}
