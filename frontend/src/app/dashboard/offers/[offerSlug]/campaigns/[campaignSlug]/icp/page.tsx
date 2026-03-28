'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { IcpBuilder } from '@/components/IcpBuilder';
import type { IcpProfile, IcpValidationResult, IcpPreviewResult, PreviewStatus } from '@/components/IcpBuilder/types';
import { createClient } from '@/lib/supabase';

// ─── Simple client-side validation ──────────────────────────────────────────

function validateProfile(profile: IcpProfile): IcpValidationResult {
  const errors: IcpValidationResult['errors'] = [];
  const warnings: IcpValidationResult['warnings'] = [];

  if (profile.companySize.idealMin >= profile.companySize.idealMax) {
    errors.push({ field: 'companySize', message: 'Ideal min must be less than ideal max' });
  }
  if (profile.companySize.hardMin != null && profile.companySize.hardMin > profile.companySize.idealMin) {
    errors.push({ field: 'companySize', message: 'Hard min must be <= ideal min' });
  }
  if (profile.companySize.hardMax != null && profile.companySize.hardMax < profile.companySize.idealMax) {
    errors.push({ field: 'companySize', message: 'Hard max must be >= ideal max' });
  }
  if (profile.industry.preferred.length === 0) {
    warnings.push({ field: 'industry', message: 'No preferred industries — scoring will be broad' });
  }
  if (profile.enrichment.seniorityLevels.length === 0) {
    errors.push({ field: 'enrichment', message: 'At least one seniority level is required' });
  }
  if (profile.enrichment.departments.length === 0) {
    errors.push({ field: 'enrichment', message: 'At least one department is required' });
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ─── Preview hook ────────────────────────────────────────────────────────────

function useIcpPreview() {
  const [result, setResult] = useState<IcpPreviewResult | null>(null);
  const [status, setStatus] = useState<PreviewStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancel = useCallback(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const run = useCallback(
    (profile: IcpProfile, source: 'db' | 'live', debounceMs = 300) => {
      // Cancel any in-flight or pending request
      cancel();

      debounceRef.current = setTimeout(async () => {
        const controller = new AbortController();
        abortRef.current = controller;

        setStatus('loading');
        setError(null);

        try {
          const resp = await fetch('/api/icp/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              icpProfile: profile,
              source,
              sampleSize: source === 'live' ? 25 : 50,
            }),
            signal: controller.signal,
          });

          if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.error || `Preview failed (${resp.status})`);
          }

          const data: IcpPreviewResult = await resp.json();

          // Only update if this request wasn't cancelled
          if (!controller.signal.aborted) {
            setResult(data);
            setStatus('success');
          }
        } catch (err: unknown) {
          if (err instanceof DOMException && err.name === 'AbortError') {
            // Request was cancelled — ignore
            return;
          }
          setError(err instanceof Error ? err.message : 'Preview failed');
          setStatus('error');
        }
      }, debounceMs);
    },
    [cancel],
  );

  // Cleanup on unmount
  useEffect(() => cancel, [cancel]);

  return { result, status, error, run, cancel };
}

// ─── Page component ─────────────────────────────────────────────────────────

export default function IcpBuilderPage() {
  const { offerSlug, campaignSlug } = useParams<{
    offerSlug: string;
    campaignSlug: string;
  }>();
  const searchParams = useSearchParams();
  const isConvert = searchParams.get('convert') === 'true';

  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [profile, setProfile] = useState<IcpProfile | null>(null);
  const [originalProfile, setOriginalProfile] = useState<IcpProfile | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [validation, setValidation] = useState<IcpValidationResult | null>(null);

  const [hasLegacyConfig, setHasLegacyConfig] = useState(false);

  // Preview state
  const preview = useIcpPreview();

  const backUrl = `/dashboard/offers/${offerSlug}/campaigns/${campaignSlug}`;

  // ── Load campaign ────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    const supabase = createClient();

    supabase
      .from('offers')
      .select('id')
      .eq('slug', offerSlug)
      .single()
      .then(({ data: offer }: { data: any }) => {
        if (cancelled || !offer) {
          if (!cancelled) setError('Offer not found');
          setLoading(false);
          return;
        }
        supabase
          .from('campaigns')
          .select('id, icp_profile, scoring_config_overrides')
          .eq('offer_id', offer.id)
          .eq('slug', campaignSlug)
          .single()
          .then(({ data: campaign }: { data: any }) => {
            if (cancelled) return;
            if (!campaign) {
              setError('Campaign not found');
              setLoading(false);
              return;
            }
            setCampaignId(campaign.id);

            if (campaign.icp_profile) {
              setProfile(campaign.icp_profile as IcpProfile);
              setOriginalProfile(campaign.icp_profile as IcpProfile);
            }

            if (campaign.scoring_config_overrides && Object.keys(campaign.scoring_config_overrides).length > 0) {
              setHasLegacyConfig(true);
            }

            setLoading(false);
          });
      });

    return () => { cancelled = true; };
  }, [offerSlug, campaignSlug]);

  // ── Validate on profile change ───────────────────────────────────────────
  useEffect(() => {
    if (profile) {
      setValidation(validateProfile(profile));
    }
  }, [profile]);

  // ── Save handler ─────────────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!campaignId || !profile) return;

    const result = validateProfile(profile);
    setValidation(result);
    if (!result.valid) return;

    setSaving(true);
    setSaveSuccess(false);

    try {
      const resp = await fetch(`/api/campaigns/${campaignId}/icp-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
      });

      if (!resp.ok) {
        const data = await resp.json();
        setError(data.error || 'Failed to save');
        return;
      }

      setOriginalProfile(profile);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      setError('Network error — could not save');
    } finally {
      setSaving(false);
    }
  }, [campaignId, profile]);

  // ── Reset handler ────────────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    if (originalProfile) {
      setProfile(originalProfile);
    } else {
      setProfile(null);
    }
  }, [originalProfile]);

  // ── Preview handlers ─────────────────────────────────────────────────────
  const handleQuickPreview = useCallback(() => {
    if (!profile) return;
    const v = validateProfile(profile);
    if (!v.valid) {
      setValidation(v);
      return;
    }
    preview.run(profile, 'db', 0); // immediate, no debounce for manual click
  }, [profile, preview]);

  const handleLivePreview = useCallback(() => {
    if (!profile) return;
    const v = validateProfile(profile);
    if (!v.valid) {
      setValidation(v);
      return;
    }
    preview.run(profile, 'live', 0);
  }, [profile, preview]);

  const previewDisabled = !profile || (validation != null && !validation.valid);

  // ── Loading state ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 text-white flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────
  if (error && !campaignId) {
    return (
      <div className="min-h-screen bg-neutral-950 text-white flex flex-col items-center justify-center gap-4">
        <AlertTriangle className="w-8 h-8 text-amber-400" />
        <p className="text-sm text-neutral-400">{error}</p>
        <Link href={backUrl} className="text-xs text-indigo-400 hover:text-indigo-300">
          Back to campaign
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Link
              href={backUrl}
              className="p-1.5 rounded-lg border border-neutral-800 text-neutral-400 hover:text-white hover:border-neutral-600 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-lg font-semibold">
                {originalProfile ? 'Edit' : 'Create'} ICP Profile
              </h1>
              <p className="text-xs text-neutral-500">
                {campaignSlug}
              </p>
            </div>
          </div>

          {/* Save status indicator */}
          {saveSuccess && (
            <div className="flex items-center gap-1.5 text-emerald-400 text-xs">
              <CheckCircle2 className="w-4 h-4" />
              Saved
            </div>
          )}
          {error && campaignId && (
            <div className="flex items-center gap-1.5 text-red-400 text-xs">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}
        </div>

        {/* Conversion banner */}
        {isConvert && hasLegacyConfig && !profile && (
          <div className="mb-4 p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-sm text-indigo-300">
            <p className="font-medium">Converting from legacy scoring config</p>
            <p className="text-xs text-indigo-400 mt-1">
              Your existing scoring overrides will remain active until you save a new ICP profile.
              Choose a preset below to start, then adjust as needed.
            </p>
          </div>
        )}

        {/* ICP Builder */}
        <IcpBuilder
          value={profile}
          onChange={setProfile}
          onSave={handleSave}
          onReset={handleReset}
          saving={saving}
          validation={validation}
          previewResult={preview.result}
          previewStatus={preview.status}
          previewError={preview.error}
          onQuickPreview={handleQuickPreview}
          onLivePreview={handleLivePreview}
          previewDisabled={previewDisabled}
        />
      </div>
    </div>
  );
}
