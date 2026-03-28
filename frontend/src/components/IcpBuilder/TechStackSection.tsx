'use client';

import React from 'react';
import type { IcpTechStackConfig } from './types';
import { TECH_SUGGESTIONS } from './constants';
import { TagInput, Section } from './shared';

interface TechStackSectionProps {
  value: IcpTechStackConfig;
  onChange: (value: IcpTechStackConfig) => void;
  mode: 'quick' | 'advanced';
}

export function TechStackSection({ value, onChange, mode }: TechStackSectionProps) {
  return (
    <Section title="Tech Stack" defaultOpen={false}>
      {mode === 'quick' ? (
        <TagInput
          label="Nice-to-Have Technologies (bonus points)"
          tags={value.niceToHave}
          onChange={(niceToHave) => onChange({ ...value, niceToHave })}
          suggestions={TECH_SUGGESTIONS}
          placeholder="Add technology..."
        />
      ) : (
        <>
          <TagInput
            label="Must-Have Technologies"
            tags={value.mustHave}
            onChange={(mustHave) => onChange({ ...value, mustHave })}
            suggestions={TECH_SUGGESTIONS}
            placeholder="Add must-have technology..."
            variant="amber"
          />
          <TagInput
            label="Nice-to-Have Technologies (bonus points)"
            tags={value.niceToHave}
            onChange={(niceToHave) => onChange({ ...value, niceToHave })}
            suggestions={TECH_SUGGESTIONS}
            placeholder="Add nice-to-have technology..."
          />
          <TagInput
            label="Avoided Technologies (penalty)"
            tags={value.avoided}
            onChange={(avoided) => onChange({ ...value, avoided })}
            placeholder="Add technology to avoid..."
            variant="danger"
          />
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-neutral-400">Must-Have Behavior</span>
            <div className="space-y-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="mustHaveBehavior"
                  checked={value.mustHaveBehavior === 'require-when-data-exists'}
                  onChange={() => onChange({ ...value, mustHaveBehavior: 'require-when-data-exists' })}
                  className="border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-xs text-neutral-300">
                  Require only when tech data exists
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="mustHaveBehavior"
                  checked={value.mustHaveBehavior === 'require-always'}
                  onChange={() => onChange({ ...value, mustHaveBehavior: 'require-always' })}
                  className="border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-xs text-neutral-300">
                  Always require (rejects companies with no tech data)
                </span>
              </label>
            </div>
          </div>
        </>
      )}
    </Section>
  );
}
