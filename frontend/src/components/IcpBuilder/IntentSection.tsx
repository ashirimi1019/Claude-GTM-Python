'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { IcpIntentConfig } from './types';
import { Section, TagInput, NumberInput } from './shared';

interface IntentSectionProps {
  value: IcpIntentConfig | undefined;
  onChange: (value: IcpIntentConfig) => void;
  mode: 'quick' | 'advanced';
}

const DEFAULT_INTENT: IcpIntentConfig = {
  topics: [],
  minScore: 50,
  requirement: 'ignored',
};

const REQUIREMENT_OPTIONS: {
  value: IcpIntentConfig['requirement'];
  label: string;
  description: string;
  badge?: string;
}[] = [
  {
    value: 'preferred',
    label: 'Preferred',
    description: 'Intent signals boost score but companies without intent data still qualify.',
    badge: 'Recommended',
  },
  {
    value: 'required',
    label: 'Required',
    description: 'Only companies with matching Bombora intent topics qualify. Significantly reduces volume.',
  },
  {
    value: 'ignored',
    label: 'Ignored',
    description: 'Intent topics are not considered. Use this if you haven\'t configured topics yet.',
  },
];

const SUGGESTED_TOPICS: string[] = [
  'Staff Augmentation',
  'IT Staffing',
  'Cloud Migration',
  'Data Engineering',
  'AI and Machine Learning',
  'Software Development Outsourcing',
];

export function IntentSection({ value, onChange, mode }: IntentSectionProps) {
  const config = value ?? DEFAULT_INTENT;

  const update = (partial: Partial<IcpIntentConfig>) => {
    onChange({ ...config, ...partial });
  };

  const hasTopics = config.topics.length > 0;
  const topicCount = config.topics.length;
  const badge =
    config.requirement === 'ignored'
      ? 'Off'
      : hasTopics
        ? `${topicCount}/6 topic${topicCount !== 1 ? 's' : ''}`
        : 'No topics';
  const badgeVariant =
    config.requirement !== 'ignored' && !hasTopics ? 'amber' as const : 'default' as const;

  return (
    <Section
      title="Intent Topics (Bombora)"
      defaultOpen={false}
      badge={badge}
      badgeVariant={badgeVariant}
    >
      {/* Requirement radio cards */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Intent Requirement</span>
        <div className="grid grid-cols-1 gap-2">
          {REQUIREMENT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => update({ requirement: opt.value })}
              className={cn(
                'w-full text-left px-3 py-2.5 rounded-lg border transition-colors',
                config.requirement === opt.value
                  ? 'bg-indigo-500/10 border-indigo-500/40'
                  : 'bg-neutral-900 border-neutral-700 hover:border-neutral-600',
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'text-xs font-medium',
                    config.requirement === opt.value ? 'text-indigo-300' : 'text-neutral-300',
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

      {/* Topic input — shown when not ignored */}
      {config.requirement !== 'ignored' && (
        <>
          <TagInput
            label={`Intent Topics (max 6 — Apollo Pro limit)`}
            tags={config.topics}
            onChange={(topics) => {
              if (topics.length <= 6) {
                update({ topics });
              }
            }}
            suggestions={SUGGESTED_TOPICS}
            placeholder="e.g. Staff Augmentation"
          />
          {topicCount >= 6 && (
            <p className="text-[10px] text-amber-400">
              Apollo Pro allows a maximum of 6 intent topics per search.
            </p>
          )}
        </>
      )}

      {/* Advanced: min score threshold */}
      {mode === 'advanced' && config.requirement !== 'ignored' && (
        <NumberInput
          label="Minimum Intent Score"
          value={config.minScore}
          onChange={(v) => update({ minScore: v ?? 50 })}
          min={0}
          max={100}
          helpText="Companies below this Bombora score get 60% reduced points (0-100 scale)"
        />
      )}
    </Section>
  );
}
