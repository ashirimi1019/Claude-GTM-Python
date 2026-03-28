'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { AlertTriangle, Check } from 'lucide-react';
import type { IcpProfile, IcpValidationResult, IcpPreviewResult, PreviewStatus } from './types';
import { FUNDING_STAGES, SENIORITY_LEVELS, DEPARTMENTS } from './constants';
import { PreviewPanel } from './PreviewPanel';

interface LiveSummaryProps {
  profile: IcpProfile;
  validation: IcpValidationResult | null;
  onSave: () => void;
  onReset: () => void;
  saving: boolean;
  // Preview props
  previewResult: IcpPreviewResult | null;
  previewStatus: PreviewStatus;
  previewError: string | null;
  onQuickPreview: () => void;
  onLivePreview: () => void;
  previewDisabled: boolean;
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

export function LiveSummary({
  profile,
  validation,
  onSave,
  onReset,
  saving,
  previewResult,
  previewStatus,
  previewError,
  onQuickPreview,
  onLivePreview,
  previewDisabled,
}: LiveSummaryProps) {
  const { companySize, industry, funding, revenue, techStack, hiringSignals, strictness, enrichment } =
    profile;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-neutral-200">Profile Summary</h3>

      {/* Company Profile */}
      <div className="space-y-1">
        <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
          Company Profile
        </h4>
        <div className="space-y-0.5 text-xs text-neutral-300">
          <p>
            <span className="text-neutral-500">Size:</span>{' '}
            {companySize.idealMin.toLocaleString()}–{companySize.idealMax.toLocaleString()} employees
            {companySize.hardMax && ` (max ${companySize.hardMax.toLocaleString()})`}
          </p>
          <p>
            <span className="text-neutral-500">Revenue:</span> {formatRevenue(revenue.minimum)}+
            {revenue.inferFromEmployees && ' (inferred when missing)'}
          </p>
          {industry.preferred.length > 0 && (
            <p>
              <span className="text-neutral-500">Industries:</span> {industry.preferred.join(', ')}
            </p>
          )}
          {industry.excluded.length > 0 && (
            <p>
              <span className="text-neutral-500 text-red-400/70">Excluded:</span>{' '}
              <span className="text-red-400/70">{industry.excluded.join(', ')}</span>
            </p>
          )}
        </div>
      </div>

      {/* Requirements */}
      <div className="space-y-1">
        <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
          Requirements
        </h4>
        <div className="space-y-0.5 text-xs text-neutral-300">
          {funding.preferred.length > 0 && (
            <p>
              <span className="text-neutral-500">Funding:</span>{' '}
              {funding.preferred.map((f) => lookupLabel(f, FUNDING_STAGES)).join(', ')}
            </p>
          )}
          {funding.excluded.length > 0 && (
            <p>
              <span className="text-red-400/70">Excluded stages:</span>{' '}
              <span className="text-red-400/70">
                {funding.excluded.map((f) => lookupLabel(f, FUNDING_STAGES)).join(', ')}
              </span>
            </p>
          )}
          {techStack.niceToHave.length > 0 && (
            <p>
              <span className="text-neutral-500">Tech:</span> {techStack.niceToHave.slice(0, 5).join(', ')}
              {techStack.niceToHave.length > 5 && ` +${techStack.niceToHave.length - 5} more`}
            </p>
          )}
          {techStack.mustHave.length > 0 && (
            <p>
              <span className="text-amber-400/70">Must-have tech:</span>{' '}
              <span className="text-amber-300">{techStack.mustHave.join(', ')}</span>
            </p>
          )}
        </div>
      </div>

      {/* Signals */}
      <div className="space-y-1">
        <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">Signals</h4>
        <div className="space-y-0.5 text-xs text-neutral-300">
          <p>
            <span className="text-neutral-500">Hiring signals:</span>{' '}
            {hiringSignals.requirement === 'required'
              ? 'Required'
              : hiringSignals.requirement === 'preferred'
                ? 'Preferred (bonus)'
                : 'Ignored'}
          </p>
          {profile.intentTopics && profile.intentTopics.requirement !== 'ignored' && (
            <p>
              <span className="text-neutral-500">Intent topics:</span>{' '}
              {profile.intentTopics.topics.length > 0
                ? `${profile.intentTopics.topics.slice(0, 3).join(', ')}${profile.intentTopics.topics.length > 3 ? ` +${profile.intentTopics.topics.length - 3} more` : ''}`
                : 'None configured'}
              {' '}({profile.intentTopics.requirement})
            </p>
          )}
        </div>
      </div>

      {/* Strictness */}
      <div className="space-y-1">
        <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
          Strictness
        </h4>
        <p className="text-xs text-neutral-300">
          <span className="text-neutral-500">Level:</span>{' '}
          {strictness.level.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          {strictness.expertOverrides?.threshold != null &&
            ` (threshold: ${strictness.expertOverrides.threshold})`}
        </p>
      </div>

      {/* Enrichment */}
      <div className="space-y-1">
        <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
          Enrichment
        </h4>
        <div className="space-y-0.5 text-xs text-neutral-300">
          <p>
            <span className="text-neutral-500">Seniority:</span>{' '}
            {enrichment.seniorityLevels.map((s) => lookupLabel(s, SENIORITY_LEVELS)).join(', ') || 'None'}
          </p>
          <p>
            <span className="text-neutral-500">Departments:</span>{' '}
            {enrichment.departments.map((d) => lookupLabel(d, DEPARTMENTS)).join(', ') || 'None'}
          </p>
          <p>
            <span className="text-neutral-500">Contacts/company:</span>{' '}
            {enrichment.maxContactsPerCompany ?? 'Unlimited'}
          </p>
          <p>
            <span className="text-neutral-500">Verified email:</span>{' '}
            {enrichment.requireVerifiedEmail ? 'Yes' : 'No'}
          </p>
        </div>
      </div>

      {/* Validation */}
      {validation && (
        <div className="space-y-2">
          {validation.errors.length > 0 && (
            <div className="space-y-1">
              {validation.errors.map((err, i) => (
                <div
                  key={i}
                  className="flex items-start gap-1.5 text-[10px] text-red-400 bg-red-500/5 border border-red-500/20 rounded px-2 py-1.5"
                >
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>
                    <span className="font-medium">{err.field}:</span> {err.message}
                  </span>
                </div>
              ))}
            </div>
          )}
          {validation.warnings.length > 0 && (
            <div className="space-y-1">
              {validation.warnings.map((warn, i) => (
                <div
                  key={i}
                  className="flex items-start gap-1.5 text-[10px] text-amber-400 bg-amber-500/5 border border-amber-500/20 rounded px-2 py-1.5"
                >
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>
                    <span className="font-medium">{warn.field}:</span> {warn.message}
                  </span>
                </div>
              ))}
            </div>
          )}
          {validation.valid && validation.errors.length === 0 && (
            <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 bg-emerald-500/5 border border-emerald-500/20 rounded px-2 py-1.5">
              <Check className="w-3 h-3" />
              Profile is valid
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2 border-t border-neutral-800">
        <button
          type="button"
          onClick={onSave}
          disabled={saving || (validation != null && !validation.valid)}
          className={cn(
            'flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors',
            'bg-indigo-600 text-white hover:bg-indigo-500',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
        <button
          type="button"
          onClick={onReset}
          disabled={saving}
          className="px-3 py-2 rounded-lg text-xs font-medium bg-neutral-800 text-neutral-300 border border-neutral-700 hover:bg-neutral-700 hover:text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Reset
        </button>
      </div>

      {/* Preview Panel — below Save */}
      <div className="pt-2 border-t border-neutral-800">
        <PreviewPanel
          result={previewResult}
          status={previewStatus}
          error={previewError}
          onQuickPreview={onQuickPreview}
          onLivePreview={onLivePreview}
          disabled={previewDisabled}
        />
      </div>
    </div>
  );
}
