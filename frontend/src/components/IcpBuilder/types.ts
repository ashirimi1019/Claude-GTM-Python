// frontend/src/components/IcpBuilder/types.ts
// Duplicated from src/types/icp.ts for frontend use (separate package boundary)

// ─── Strictness ───────────────────────────────────────

export type StrictnessLevel = 'broad' | 'balanced' | 'strict' | 'very_strict';

export const STRICTNESS_ORDER: Record<StrictnessLevel, number> = {
  broad: 0,
  balanced: 1,
  strict: 2,
  very_strict: 3,
};

// ─── Company Size ─────────────────────────────────────

export type SizePreset = 'startup' | 'smb' | 'mid-market' | 'enterprise' | 'any';

export interface IcpCompanySize {
  preset: SizePreset | null;
  hardMin: number | null;
  idealMin: number;
  idealMax: number;
  hardMax: number | null;
  rejectOutsideHardRange: boolean;
  unknownSizeBehavior: 'allow-with-penalty' | 'reject';
}

// ─── Industry ─────────────────────────────────────────

export interface IcpIndustryConfig {
  preferred: string[];
  excluded: string[];
}

// ─── Funding ──────────────────────────────────────────

export interface IcpFundingConfig {
  preferred: string[];
  excluded: string[];
  acceptable: string[] | null;
}

// ─── Revenue ──────────────────────────────────────────

export interface IcpRevenueConfig {
  minimum: number;
  inferFromEmployees: boolean;
}

// ─── Tech Stack ───────────────────────────────────────

export interface IcpTechStackConfig {
  mustHave: string[];
  niceToHave: string[];
  avoided: string[];
  mustHaveBehavior: 'require-when-data-exists' | 'require-always';
  niceToHaveWeights: Record<string, number> | null;
}

// ─── Hiring Signals ───────────────────────────────────

export interface IcpHiringSignalConfig {
  requirement: 'required' | 'preferred' | 'ignored';
  qualityWeights: { freshnessWeight: number; intensityWeight: number } | null;
}

// ─── Intent Topics (Bombora via Apollo Pro) ──────────

export interface IcpIntentConfig {
  /** Bombora intent topic names to filter by (max 6 on Apollo Pro) */
  topics: string[];
  /** Minimum composite score (0-100) to award full points; below this = partial credit */
  minScore: number;
  /** Whether to require intent signal match as a hard filter or just use for scoring */
  requirement: 'required' | 'preferred' | 'ignored';
}

// ─── Strictness Config ────────────────────────────────

export interface IcpExpertOverrides {
  threshold: number | null;
  dataQuality: 'accept-incomplete' | 'prefer-complete' | 'require-complete' | null;
  requirePreferredFunding: boolean | null;
  requirePreferredIndustries: boolean | null;
  rejectMissingTech: boolean | null;
  rejectMissingRevenue: boolean | null;
  maxCriticalUnknowns: number | null;
}

export interface IcpStrictnessConfig {
  level: StrictnessLevel;
  expertOverrides: IcpExpertOverrides | null;
}

// ─── Enrichment ───────────────────────────────────────

export interface IcpEnrichmentConfig {
  seniorityLevels: string[];
  departments: string[];
  secondaryDepartments: string[];
  titleKeywords: string[];
  maxContactsPerCompany: 1 | 3 | 5 | null;
  requireVerifiedEmail: boolean;
  rankingStrategy: 'relevance' | 'seniority' | 'hybrid';
}

// ─── Top-Level Profile ────────────────────────────────

export interface IcpProfile {
  version: 1;
  basePreset: 'staffing' | 'ai-data-consulting' | 'cloud-software-delivery' | null;
  mode: 'quick' | 'advanced';
  companySize: IcpCompanySize;
  industry: IcpIndustryConfig;
  funding: IcpFundingConfig;
  revenue: IcpRevenueConfig;
  techStack: IcpTechStackConfig;
  hiringSignals: IcpHiringSignalConfig;
  /** Bombora intent topics via Apollo Pro (optional — backward compatible) */
  intentTopics?: IcpIntentConfig;
  strictness: IcpStrictnessConfig;
  enrichment: IcpEnrichmentConfig;
}

// ─── Validation Types ─────────────────────────────────

export interface IcpValidationError {
  field: string;
  message: string;
}

export interface IcpValidationWarning {
  field: string;
  message: string;
}

export interface IcpValidationResult {
  valid: boolean;
  errors: IcpValidationError[];
  warnings: IcpValidationWarning[];
}

// ─── Preview Result Types ────────────────────────────

export type PreviewSource = 'inline' | 'db' | 'live';

export interface IcpPreviewResult {
  summary: {
    totalCompanies: number;
    qualified: number;
    rejected: number;
    qualificationRate: number;
  };
  rejectionBreakdown: {
    'hard-filter': number;
    confidence: number;
    scoring: number;
    'after-enrichment': number;
  };
  topRejectionReasons: Array<{ reason: string; count: number }>;
  tierDistribution: { A: number; B: number; C: number };
  confidenceStats: { mean: number; min: number; max: number };
  scoreStats: {
    min: number;
    max: number;
    median: number;
    mean: number;
  } | null;
  effectiveConfig: {
    threshold: number;
    strictnessLevel: string;
    maxScore: number;
    hiringSignalMax: number;
  };
  sampleTraces: IcpPreviewTrace[];
  twoStageInfo?: {
    /** True when preview only ran Stage 1 (no enrichment in preview mode) */
    isSearchStageOnly: boolean;
    /** Number of companies that passed Stage 1 broad screening */
    stage1Shortlisted: number;
    /** Explanatory note for the operator */
    note: string;
  };
  _meta?: { source: PreviewSource; companiesEvaluated: number };
}

export interface IcpPreviewTrace {
  companyId: string;
  companyName: string;
  outcome: 'qualified' | 'rejected-hard-filter' | 'rejected-confidence' | 'rejected-scoring';
  tier: 'A' | 'B' | 'C' | null;
  confidence: {
    overall: number;
    criticalUnknowns: number;
  };
  scoring: {
    total: number;
    maxPossible: number;
    threshold: number;
    zeroDimensions: string[];
  } | null;
  hardFilters: Array<{
    gate: string;
    passed: boolean;
    reason: string;
    companyValue: string | null;
  }>;
  summary: string;
}

export type PreviewStatus = 'idle' | 'loading' | 'success' | 'error';
