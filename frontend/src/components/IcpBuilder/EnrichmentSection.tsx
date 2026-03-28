'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Info } from 'lucide-react';
import type { IcpEnrichmentConfig } from './types';
import { SENIORITY_LEVELS, DEPARTMENTS, CONTACT_CAP_OPTIONS } from './constants';
import { PillButton, TagInput, Section } from './shared';

interface EnrichmentSectionProps {
  value: IcpEnrichmentConfig;
  onChange: (value: IcpEnrichmentConfig) => void;
  mode: 'quick' | 'advanced';
}

export function EnrichmentSection({ value, onChange, mode }: EnrichmentSectionProps) {
  const toggleSeniority = (level: string) => {
    const current = value.seniorityLevels;
    const next = current.includes(level)
      ? current.filter((l) => l !== level)
      : [...current, level];
    onChange({ ...value, seniorityLevels: next });
  };

  const toggleDepartment = (dept: string) => {
    const current = value.departments;
    const next = current.includes(dept)
      ? current.filter((d) => d !== dept)
      : [...current, dept];
    onChange({ ...value, departments: next });
  };

  return (
    <Section title="Enrichment & Contacts" defaultOpen={false}>
      {/* Info callout */}
      <div className="flex items-start gap-2 px-3 py-2 rounded-lg bg-indigo-500/5 border border-indigo-500/20">
        <Info className="w-3.5 h-3.5 text-indigo-400 mt-0.5 shrink-0" />
        <p className="text-[10px] text-indigo-300/80">
          Enrichment runs AFTER qualification — only for companies that pass ICP scoring.
        </p>
      </div>

      {/* Seniority levels */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Seniority Levels</span>
        <div className="flex flex-wrap gap-1.5">
          {SENIORITY_LEVELS.map((level) => (
            <PillButton
              key={level.value}
              active={value.seniorityLevels.includes(level.value)}
              onClick={() => toggleSeniority(level.value)}
            >
              {level.label}
            </PillButton>
          ))}
        </div>
      </div>

      {/* Departments */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Departments</span>
        <div className="flex flex-wrap gap-1.5">
          {DEPARTMENTS.map((dept) => (
            <PillButton
              key={dept.value}
              active={value.departments.includes(dept.value)}
              onClick={() => toggleDepartment(dept.value)}
            >
              {dept.label}
            </PillButton>
          ))}
        </div>
      </div>

      {/* Title keywords */}
      <TagInput
        label="Title Keywords"
        tags={value.titleKeywords}
        onChange={(titleKeywords) => onChange({ ...value, titleKeywords })}
        placeholder="Add title keyword..."
        suggestions={['CTO', 'VP Engineering', 'VP Data', 'Head of AI', 'Director of Engineering']}
      />

      {/* Contact cap */}
      <div className="space-y-1.5">
        <span className="text-xs font-medium text-neutral-400">Contacts Per Company</span>
        <div className="flex gap-1.5">
          {CONTACT_CAP_OPTIONS.map((opt) => (
            <PillButton
              key={opt.label}
              active={value.maxContactsPerCompany === opt.value}
              onClick={() =>
                onChange({
                  ...value,
                  maxContactsPerCompany: opt.value as 1 | 3 | 5 | null,
                })
              }
            >
              {opt.label}
            </PillButton>
          ))}
        </div>
      </div>

      {/* Verified email */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={value.requireVerifiedEmail}
          onChange={(e) => onChange({ ...value, requireVerifiedEmail: e.target.checked })}
          className="rounded border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
        />
        <span className="text-xs text-neutral-300">Require verified email</span>
      </label>

      {/* Advanced: ranking strategy */}
      {mode === 'advanced' && (
        <div className="space-y-1.5">
          <span className="text-xs font-medium text-neutral-400">Ranking Strategy</span>
          <div className="space-y-1">
            {(
              [
                { value: 'relevance', label: 'Relevance', desc: 'Rank by title/department match' },
                { value: 'seniority', label: 'Seniority', desc: 'Rank by seniority level' },
                { value: 'hybrid', label: 'Hybrid', desc: 'Balance of relevance and seniority' },
              ] as const
            ).map((opt) => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="rankingStrategy"
                  checked={value.rankingStrategy === opt.value}
                  onChange={() => onChange({ ...value, rankingStrategy: opt.value })}
                  className="border-neutral-700 bg-neutral-900 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-xs text-neutral-300">{opt.label}</span>
                <span className="text-[10px] text-neutral-500">— {opt.desc}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </Section>
  );
}
