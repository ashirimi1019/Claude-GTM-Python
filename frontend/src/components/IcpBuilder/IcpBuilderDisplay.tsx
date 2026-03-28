'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { ChevronRight } from 'lucide-react';
import type { IcpProfile } from './types';
import { FUNDING_STAGES } from './constants';

interface IcpBuilderDisplayProps {
  profile: IcpProfile;
  updatedAt: string | null;
  editUrl: string;
}

function lookupLabel(value: string, list: readonly { value: string; label: string }[]): string {
  return list.find((item) => item.value === value)?.label ?? value;
}

function formatRevenue(amount: number): string {
  if (amount === 0) return 'Any';
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(0)}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
  return `$${amount}`;
}

export function IcpBuilderDisplay({ profile, updatedAt, editUrl }: IcpBuilderDisplayProps) {
  const { companySize, industry, funding, revenue, strictness, techStack, hiringSignals, enrichment } =
    profile;

  return (
    <div className="p-4 rounded-lg bg-neutral-800 border border-neutral-700 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-xs font-semibold text-neutral-200">ICP Profile</h4>
          {updatedAt && (
            <p className="text-[10px] text-neutral-500">
              Updated {new Date(updatedAt).toLocaleDateString()}
            </p>
          )}
        </div>
        <a
          href={editUrl}
          className="inline-flex items-center gap-1 text-[10px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          Edit ICP <ChevronRight className="w-3 h-3" />
        </a>
      </div>

      {/* Key metrics pills */}
      <div className="flex flex-wrap gap-1.5">
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          {companySize.idealMin.toLocaleString()}–{companySize.idealMax.toLocaleString()} employees
        </span>
        {companySize.hardMax && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400">
            max {companySize.hardMax.toLocaleString()}
          </span>
        )}
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-700 border border-neutral-600 text-neutral-300">
          Rev: {formatRevenue(revenue.minimum)}+
        </span>
        <span
          className={cn(
            'text-[10px] px-2 py-0.5 rounded-full border',
            strictness.level === 'strict' || strictness.level === 'very_strict'
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : 'bg-neutral-700 border-neutral-600 text-neutral-300',
          )}
        >
          {strictness.level.replace('_', ' ')}
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-neutral-700 border border-neutral-600 text-neutral-300">
          Signals: {hiringSignals.requirement}
        </span>
      </div>

      {/* Compact details */}
      <div className="space-y-1 text-[10px]">
        {funding.preferred.length > 0 && (
          <div className="flex flex-wrap gap-1">
            <span className="text-neutral-500">Funding:</span>
            {funding.preferred.map((f) => (
              <span
                key={f}
                className="px-1.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-400"
              >
                {lookupLabel(f, FUNDING_STAGES)}
              </span>
            ))}
          </div>
        )}
        {industry.preferred.length > 0 && (
          <div className="flex flex-wrap gap-1">
            <span className="text-neutral-500">Industries:</span>
            {industry.preferred.slice(0, 4).map((ind) => (
              <span key={ind} className="px-1.5 py-0.5 rounded bg-neutral-700 text-neutral-400">
                {ind}
              </span>
            ))}
            {industry.preferred.length > 4 && (
              <span className="text-neutral-500">+{industry.preferred.length - 4} more</span>
            )}
          </div>
        )}
        {techStack.niceToHave.length > 0 && (
          <div className="flex flex-wrap gap-1">
            <span className="text-neutral-500">Tech:</span>
            {techStack.niceToHave.slice(0, 5).map((t) => (
              <span key={t} className="px-1.5 py-0.5 rounded bg-neutral-700 text-neutral-400">
                {t}
              </span>
            ))}
            {techStack.niceToHave.length > 5 && (
              <span className="text-neutral-500">+{techStack.niceToHave.length - 5} more</span>
            )}
          </div>
        )}
        <p className="text-neutral-500">
          Contacts: {enrichment.maxContactsPerCompany ?? 'unlimited'}/company
          {enrichment.requireVerifiedEmail ? ', verified only' : ''}
        </p>
      </div>
    </div>
  );
}
