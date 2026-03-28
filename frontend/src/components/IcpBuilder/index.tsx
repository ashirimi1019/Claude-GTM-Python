'use client';

import React, { useCallback } from 'react';
import { cn } from '@/lib/utils';
import type {
  IcpProfile,
  IcpCompanySize,
  IcpIndustryConfig,
  IcpFundingConfig,
  IcpRevenueConfig,
  IcpTechStackConfig,
  IcpHiringSignalConfig,
  IcpIntentConfig,
  IcpStrictnessConfig,
  IcpEnrichmentConfig,
  IcpValidationResult,
  IcpPreviewResult,
  PreviewStatus,
} from './types';
import { VERTICAL_PRESETS, getPresetProfile } from './presets';
import { PillButton } from './shared';
import { SizeSection } from './SizeSection';
import { IndustrySection } from './IndustrySection';
import { FundingRevenueSection } from './FundingRevenueSection';
import { TechStackSection } from './TechStackSection';
import { SignalsSection } from './SignalsSection';
import { IntentSection } from './IntentSection';
import { StrictnessSection } from './StrictnessSection';
import { EnrichmentSection } from './EnrichmentSection';
import { LiveSummary } from './LiveSummary';

interface IcpBuilderProps {
  value: IcpProfile | null;
  onChange: (profile: IcpProfile) => void;
  onSave: () => void;
  onReset?: () => void;
  saving: boolean;
  validation: IcpValidationResult | null;
  // Preview
  previewResult: IcpPreviewResult | null;
  previewStatus: PreviewStatus;
  previewError: string | null;
  onQuickPreview: () => void;
  onLivePreview: () => void;
  previewDisabled: boolean;
}

/** Default empty profile for initial state */
function defaultProfile(): IcpProfile {
  return {
    version: 1,
    basePreset: null,
    mode: 'quick',
    companySize: {
      preset: 'mid-market',
      hardMin: 100,
      idealMin: 200,
      idealMax: 2000,
      hardMax: 5000,
      rejectOutsideHardRange: true,
      unknownSizeBehavior: 'allow-with-penalty',
    },
    industry: { preferred: [], excluded: [] },
    funding: { preferred: [], excluded: [], acceptable: null },
    revenue: { minimum: 10_000_000, inferFromEmployees: true },
    techStack: {
      mustHave: [],
      niceToHave: [],
      avoided: [],
      mustHaveBehavior: 'require-when-data-exists',
      niceToHaveWeights: null,
    },
    hiringSignals: {
      requirement: 'preferred',
      qualityWeights: { freshnessWeight: 0.6, intensityWeight: 0.4 },
    },
    strictness: { level: 'balanced', expertOverrides: null },
    enrichment: {
      seniorityLevels: ['c_suite', 'vp', 'director', 'head'],
      departments: ['engineering', 'data'],
      secondaryDepartments: [],
      titleKeywords: [],
      maxContactsPerCompany: 3,
      requireVerifiedEmail: true,
      rankingStrategy: 'hybrid',
    },
  };
}

export function IcpBuilder({
  value,
  onChange,
  onSave,
  onReset,
  saving,
  validation,
  previewResult,
  previewStatus,
  previewError,
  onQuickPreview,
  onLivePreview,
  previewDisabled,
}: IcpBuilderProps) {
  const profile = value ?? defaultProfile();
  const mode = profile.mode;

  const update = useCallback(
    (partial: Partial<IcpProfile>) => {
      onChange({ ...profile, ...partial });
    },
    [profile, onChange],
  );

  const handlePresetSelect = (key: string) => {
    const preset = getPresetProfile(key);
    if (preset) {
      preset.mode = mode; // preserve current mode
      onChange(preset);
    }
  };

  const handleModeToggle = () => {
    const newMode = mode === 'quick' ? 'advanced' : 'quick';
    update({ mode: newMode });
  };

  const handleReset = () => {
    if (onReset) {
      onReset();
    } else {
      onChange(defaultProfile());
    }
  };

  return (
    <div className="space-y-4">
      {/* Top bar: mode toggle + preset selector */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Mode toggle */}
        <div className="flex items-center gap-1 bg-neutral-900 border border-neutral-700 rounded-lg p-0.5">
          <button
            type="button"
            onClick={() => mode !== 'quick' && handleModeToggle()}
            className={cn(
              'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              mode === 'quick'
                ? 'bg-indigo-600 text-white'
                : 'text-neutral-400 hover:text-neutral-300',
            )}
          >
            Quick
          </button>
          <button
            type="button"
            onClick={() => mode !== 'advanced' && handleModeToggle()}
            className={cn(
              'px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              mode === 'advanced'
                ? 'bg-indigo-600 text-white'
                : 'text-neutral-400 hover:text-neutral-300',
            )}
          >
            Advanced
          </button>
        </div>

        {/* Preset selector */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-neutral-500">Preset:</span>
          {Object.entries(VERTICAL_PRESETS).map(([key, preset]) => (
            <PillButton
              key={key}
              active={profile.basePreset === key}
              onClick={() => handlePresetSelect(key)}
            >
              {preset.label}
            </PillButton>
          ))}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-6">
        {/* Left: sections (scrollable) */}
        <div className="flex-1 space-y-3 min-w-0">
          <SizeSection
            value={profile.companySize}
            onChange={(companySize: IcpCompanySize) => update({ companySize })}
            mode={mode}
          />
          <IndustrySection
            value={profile.industry}
            onChange={(industry: IcpIndustryConfig) => update({ industry })}
            mode={mode}
            strictnessLevel={profile.strictness.level}
          />
          <FundingRevenueSection
            fundingValue={profile.funding}
            revenueValue={profile.revenue}
            onFundingChange={(funding: IcpFundingConfig) => update({ funding })}
            onRevenueChange={(revenue: IcpRevenueConfig) => update({ revenue })}
            mode={mode}
            strictnessLevel={profile.strictness.level}
          />
          <TechStackSection
            value={profile.techStack}
            onChange={(techStack: IcpTechStackConfig) => update({ techStack })}
            mode={mode}
          />
          <SignalsSection
            value={profile.hiringSignals}
            onChange={(hiringSignals: IcpHiringSignalConfig) => update({ hiringSignals })}
            mode={mode}
          />
          <IntentSection
            value={profile.intentTopics}
            onChange={(intentTopics: IcpIntentConfig) => update({ intentTopics })}
            mode={mode}
          />
          <StrictnessSection
            value={profile.strictness}
            onChange={(strictness: IcpStrictnessConfig) => update({ strictness })}
            mode={mode}
          />
          <EnrichmentSection
            value={profile.enrichment}
            onChange={(enrichment: IcpEnrichmentConfig) => update({ enrichment })}
            mode={mode}
          />
        </div>

        {/* Right: sticky LiveSummary */}
        <div className="hidden lg:block w-80 shrink-0">
          <div className="sticky top-4 p-4 rounded-lg bg-neutral-900 border border-neutral-800 max-h-[calc(100vh-2rem)] overflow-y-auto">
            <LiveSummary
              profile={profile}
              validation={validation}
              onSave={onSave}
              onReset={handleReset}
              saving={saving}
              previewResult={previewResult}
              previewStatus={previewStatus}
              previewError={previewError}
              onQuickPreview={onQuickPreview}
              onLivePreview={onLivePreview}
              previewDisabled={previewDisabled}
            />
          </div>
        </div>
      </div>

      {/* Mobile: save/reset at bottom (summary hidden on small screens) */}
      <div className="lg:hidden pt-2 border-t border-neutral-800">
        <LiveSummary
          profile={profile}
          validation={validation}
          onSave={onSave}
          onReset={handleReset}
          saving={saving}
          previewResult={previewResult}
          previewStatus={previewStatus}
          previewError={previewError}
          onQuickPreview={onQuickPreview}
          onLivePreview={onLivePreview}
          previewDisabled={previewDisabled}
        />
      </div>
    </div>
  );
}
