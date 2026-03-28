// frontend/src/components/IcpBuilder/constants.ts

export const FUNDING_STAGES = [
  { value: 'pre_seed', label: 'Pre-Seed' },
  { value: 'seed', label: 'Seed' },
  { value: 'series_a', label: 'Series A' },
  { value: 'series_b', label: 'Series B' },
  { value: 'series_c', label: 'Series C' },
  { value: 'series_d_plus', label: 'Series D+' },
  { value: 'growth', label: 'Growth' },
  { value: 'public', label: 'Public' },
  { value: 'bootstrapped', label: 'Bootstrapped' },
] as const;

export const SENIORITY_LEVELS = [
  { value: 'c_suite', label: 'C-Suite' },
  { value: 'vp', label: 'VP' },
  { value: 'director', label: 'Director' },
  { value: 'head', label: 'Head/Lead' },
  { value: 'manager', label: 'Manager' },
  { value: 'ic', label: 'Individual Contributor' },
] as const;

export const DEPARTMENTS = [
  { value: 'engineering', label: 'Engineering' },
  { value: 'data', label: 'Data' },
  { value: 'ai_ml', label: 'AI/ML' },
  { value: 'platform_devops', label: 'Platform/DevOps' },
  { value: 'it_infrastructure', label: 'IT/Infrastructure' },
  { value: 'product', label: 'Product' },
  { value: 'talent_hr', label: 'Talent/HR' },
] as const;

export const INDUSTRY_SUGGESTIONS = [
  'SaaS', 'Financial Services', 'Healthcare', 'E-commerce', 'Manufacturing',
  'Media', 'Fintech', 'Logistics', 'Insurance', 'Real Estate', 'Telecom',
  'Energy', 'Retail', 'Automotive', 'Pharmaceuticals', 'Cybersecurity',
  'EdTech', 'AgTech', 'CleanTech', 'BioTech',
];

export const INDUSTRY_EXCLUSION_SUGGESTIONS = [
  'Government', 'Military', 'Education', 'Non-profit', 'Religious',
  'Staffing', 'Recruiting', 'Consulting',
];

export const TECH_SUGGESTIONS = [
  'Snowflake', 'Databricks', 'dbt', 'Airflow', 'Spark', 'Kafka',
  'Kubernetes', 'Docker', 'Terraform', 'AWS', 'GCP', 'Azure',
  'Python', 'Java', 'Go', 'React', 'Node.js', 'PostgreSQL',
  'MongoDB', 'Redis', 'Elasticsearch', 'MLflow', 'Tableau', 'Looker',
];

export const REVENUE_OPTIONS = [
  { value: 0, label: 'Any' },
  { value: 1_000_000, label: '$1M' },
  { value: 5_000_000, label: '$5M' },
  { value: 10_000_000, label: '$10M' },
  { value: 25_000_000, label: '$25M' },
  { value: 50_000_000, label: '$50M' },
  { value: 100_000_000, label: '$100M' },
] as const;

export const CONTACT_CAP_OPTIONS = [
  { value: 1, label: '1' },
  { value: 3, label: '3' },
  { value: 5, label: '5' },
  { value: null, label: 'Unlimited' },
] as const;

// Size preset boundaries for quick mode
export const SIZE_PRESET_VALUES: Record<string, { hardMin: number | null; idealMin: number; idealMax: number; hardMax: number | null }> = {
  startup: { hardMin: 10, idealMin: 20, idealMax: 100, hardMax: 200 },
  smb: { hardMin: 50, idealMin: 100, idealMax: 500, hardMax: 1000 },
  'mid-market': { hardMin: 100, idealMin: 200, idealMax: 2000, hardMax: 5000 },
  enterprise: { hardMin: 500, idealMin: 1000, idealMax: 10000, hardMax: 50000 },
  any: { hardMin: null, idealMin: 1, idealMax: 50000, hardMax: null },
};
