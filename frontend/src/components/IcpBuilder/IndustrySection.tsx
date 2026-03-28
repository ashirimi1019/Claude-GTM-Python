'use client';

import React from 'react';
import type { IcpIndustryConfig, StrictnessLevel } from './types';
import { STRICTNESS_ORDER } from './types';
import { INDUSTRY_SUGGESTIONS, INDUSTRY_EXCLUSION_SUGGESTIONS } from './constants';
import { TagInput, Section } from './shared';

interface IndustrySectionProps {
  value: IcpIndustryConfig;
  onChange: (value: IcpIndustryConfig) => void;
  mode: 'quick' | 'advanced';
  strictnessLevel: StrictnessLevel;
}

export function IndustrySection({ value, onChange, mode, strictnessLevel }: IndustrySectionProps) {
  const isStrictPlus = STRICTNESS_ORDER[strictnessLevel] >= STRICTNESS_ORDER.strict;

  return (
    <Section
      title="Industry"
      defaultOpen={true}
      badge={isStrictPlus ? 'Required in Strict+' : undefined}
      badgeVariant="amber"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TagInput
          label="Preferred Industries"
          tags={value.preferred}
          onChange={(preferred) => onChange({ ...value, preferred })}
          suggestions={INDUSTRY_SUGGESTIONS}
          placeholder="Add preferred industry..."
          variant="default"
        />
        <TagInput
          label="Excluded Industries"
          tags={value.excluded}
          onChange={(excluded) => onChange({ ...value, excluded })}
          suggestions={INDUSTRY_EXCLUSION_SUGGESTIONS}
          placeholder="Add excluded industry..."
          variant="danger"
        />
      </div>
      {isStrictPlus && value.preferred.length === 0 && (
        <p className="text-[10px] text-amber-400">
          At Strict+ strictness, companies not in a preferred industry may be penalized or rejected.
          Consider adding preferred industries.
        </p>
      )}
    </Section>
  );
}
