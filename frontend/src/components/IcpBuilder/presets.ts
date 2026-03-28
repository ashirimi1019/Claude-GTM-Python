// frontend/src/components/IcpBuilder/presets.ts

import type { IcpProfile } from './types';

export const VERTICAL_PRESETS: Record<string, { label: string; profile: IcpProfile }> = {
  staffing: {
    label: 'Staffing (TaaS)',
    profile: {
      version: 1,
      basePreset: 'staffing',
      mode: 'quick',
      companySize: {
        preset: 'mid-market',
        hardMin: 50,
        idealMin: 200,
        idealMax: 2000,
        hardMax: 5000,
        rejectOutsideHardRange: true,
        unknownSizeBehavior: 'allow-with-penalty',
      },
      industry: {
        preferred: ['SaaS', 'Fintech', 'Financial Services', 'E-commerce', 'Healthcare'],
        excluded: ['Staffing', 'Recruiting', 'Government', 'Military', 'Non-profit', 'Religious'],
      },
      funding: {
        preferred: ['series_a', 'series_b', 'series_c'],
        excluded: ['pre_seed'],
        acceptable: ['seed', 'series_d_plus', 'growth'],
      },
      revenue: {
        minimum: 10_000_000,
        inferFromEmployees: true,
      },
      techStack: {
        mustHave: [],
        niceToHave: ['Spark', 'Airflow', 'dbt', 'Snowflake', 'Databricks', 'Kafka', 'Kubernetes', 'Terraform'],
        avoided: [],
        mustHaveBehavior: 'require-when-data-exists',
        niceToHaveWeights: null,
      },
      hiringSignals: {
        requirement: 'preferred',
        qualityWeights: { freshnessWeight: 0.6, intensityWeight: 0.4 },
      },
      strictness: {
        level: 'balanced',
        expertOverrides: null,
      },
      enrichment: {
        seniorityLevels: ['c_suite', 'vp', 'director', 'head'],
        departments: ['engineering', 'data', 'talent_hr'],
        secondaryDepartments: ['product'],
        titleKeywords: ['CTO', 'VP Engineering', 'Head of Data', 'Director of Engineering', 'VP Talent'],
        maxContactsPerCompany: 3,
        requireVerifiedEmail: true,
        rankingStrategy: 'hybrid',
      },
    },
  },
  'ai-data-consulting': {
    label: 'AI & Data Consulting',
    profile: {
      version: 1,
      basePreset: 'ai-data-consulting',
      mode: 'quick',
      companySize: {
        preset: 'mid-market',
        hardMin: 100,
        idealMin: 200,
        idealMax: 5000,
        hardMax: 10000,
        rejectOutsideHardRange: true,
        unknownSizeBehavior: 'allow-with-penalty',
      },
      industry: {
        preferred: ['SaaS', 'Fintech', 'Financial Services', 'Healthcare', 'E-commerce', 'Insurance'],
        excluded: ['Government', 'Military', 'Staffing', 'Recruiting', 'Non-profit'],
      },
      funding: {
        preferred: ['series_b', 'series_c', 'series_d_plus'],
        excluded: ['pre_seed'],
        acceptable: ['series_a', 'growth', 'public'],
      },
      revenue: {
        minimum: 20_000_000,
        inferFromEmployees: true,
      },
      techStack: {
        mustHave: [],
        niceToHave: ['Databricks', 'Snowflake', 'Spark', 'dbt', 'Airflow', 'MLflow', 'Kafka', 'Python'],
        avoided: [],
        mustHaveBehavior: 'require-when-data-exists',
        niceToHaveWeights: null,
      },
      hiringSignals: {
        requirement: 'preferred',
        qualityWeights: { freshnessWeight: 0.6, intensityWeight: 0.4 },
      },
      strictness: {
        level: 'balanced',
        expertOverrides: null,
      },
      enrichment: {
        seniorityLevels: ['c_suite', 'vp', 'director', 'head'],
        departments: ['data', 'ai_ml', 'engineering'],
        secondaryDepartments: ['platform_devops', 'product'],
        titleKeywords: ['CDO', 'CTO', 'VP Data', 'Head of AI', 'Director of Data Engineering', 'VP Engineering'],
        maxContactsPerCompany: 3,
        requireVerifiedEmail: true,
        rankingStrategy: 'hybrid',
      },
    },
  },
  'cloud-software-delivery': {
    label: 'Cloud & Software Delivery',
    profile: {
      version: 1,
      basePreset: 'cloud-software-delivery',
      mode: 'quick',
      companySize: {
        preset: 'mid-market',
        hardMin: 50,
        idealMin: 100,
        idealMax: 5000,
        hardMax: 10000,
        rejectOutsideHardRange: true,
        unknownSizeBehavior: 'allow-with-penalty',
      },
      industry: {
        preferred: ['SaaS', 'Fintech', 'E-commerce', 'Healthcare', 'Cybersecurity', 'Logistics'],
        excluded: ['Government', 'Military', 'Staffing', 'Recruiting', 'Non-profit'],
      },
      funding: {
        preferred: ['series_b', 'series_c', 'series_d_plus'],
        excluded: ['pre_seed'],
        acceptable: ['series_a', 'growth', 'public'],
      },
      revenue: {
        minimum: 20_000_000,
        inferFromEmployees: true,
      },
      techStack: {
        mustHave: [],
        niceToHave: ['Kubernetes', 'Docker', 'Terraform', 'AWS', 'GCP', 'Azure', 'Go', 'React', 'Node.js'],
        avoided: [],
        mustHaveBehavior: 'require-when-data-exists',
        niceToHaveWeights: null,
      },
      hiringSignals: {
        requirement: 'preferred',
        qualityWeights: { freshnessWeight: 0.6, intensityWeight: 0.4 },
      },
      strictness: {
        level: 'balanced',
        expertOverrides: null,
      },
      enrichment: {
        seniorityLevels: ['c_suite', 'vp', 'director', 'head'],
        departments: ['engineering', 'platform_devops', 'it_infrastructure'],
        secondaryDepartments: ['data', 'product'],
        titleKeywords: ['CTO', 'VP Engineering', 'VP Platform', 'Head of Infrastructure', 'Director of DevOps'],
        maxContactsPerCompany: 3,
        requireVerifiedEmail: true,
        rankingStrategy: 'hybrid',
      },
    },
  },
};

/** Get a deep copy of a preset profile */
export function getPresetProfile(key: string): IcpProfile | null {
  const preset = VERTICAL_PRESETS[key];
  if (!preset) return null;
  return JSON.parse(JSON.stringify(preset.profile)) as IcpProfile;
}
