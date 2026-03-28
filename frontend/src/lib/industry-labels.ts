/**
 * Map SIC codes and Apollo industry slugs to human-readable labels.
 * Apollo returns industry as either a human name, SIC code number, or slug.
 */

const SIC_CODES: Record<string, string> = {
  '7371': 'Computer Services',
  '7372': 'Software & Programming',
  '7373': 'Computer Integrated Systems',
  '7374': 'Computer Processing & Data',
  '7375': 'Computer Rental & Leasing',
  '7376': 'Computer Maintenance',
  '7377': 'Computer Rental',
  '7378': 'Computer Maintenance & Repair',
  '7379': 'Computer Services (NEC)',
  '7381': 'Security Services',
  '7382': 'Security Systems',
  '7383': 'News Syndicates',
  '7384': 'Photofinishing Labs',
  '7389': 'Business Services (NEC)',
  '2711': 'Publishing & Printing',
  '2741': 'Miscellaneous Publishing',
  '3577': 'Computer Peripherals',
  '3669': 'Communications Equipment',
  '3674': 'Semiconductors',
  '3679': 'Electronic Components',
  '3812': 'Defense Electronics',
  '4813': 'Telephone Communications',
  '4899': 'Communications (NEC)',
  '5045': 'Computer Equipment (Wholesale)',
  '5065': 'Electronic Parts (Wholesale)',
  '5112': 'Stationery & Office Supplies',
  '5734': 'Computer & Software Stores',
  '6021': 'National Commercial Banks',
  '6022': 'State Commercial Banks',
  '6035': 'Savings Institutions',
  '6099': 'Financial Services',
  '6141': 'Personal Credit',
  '6159': 'Federal Loan Agencies',
  '6162': 'Mortgage Bankers',
  '6199': 'Finance Services',
  '6211': 'Security Brokers & Dealers',
  '6311': 'Insurance Carriers',
  '6399': 'Insurance Services',
  '6411': 'Insurance Agents',
  '6512': 'Real Estate Operators',
  '6531': 'Real Estate Agents',
  '6552': 'Real Estate Developers',
  '6726': 'Investment Offices',
  '7011': 'Hotels & Motels',
  '7812': 'Motion Picture Production',
  '7941': 'Professional Sports Clubs',
  '8011': 'Physicians',
  '8021': 'Dentists',
  '8049': 'Health Practitioners',
  '8051': 'Skilled Nursing',
  '8062': 'Hospitals',
  '8071': 'Health Services',
  '8099': 'Health Services (NEC)',
  '8111': 'Legal Services',
  '8200': 'Education',
  '8299': 'Schools & Training',
  '8711': 'Engineering Services',
  '8712': 'Architectural Services',
  '8721': 'Accounting & Auditing',
  '8731': 'R&D Physical Sciences',
  '8742': 'Management Consulting',
  '8748': 'Business Consulting',
  '8999': 'Services (NEC)',
};

/**
 * Convert an Apollo industry value to a human-readable label.
 * Handles: SIC codes (numeric), human names (pass-through), null/empty.
 */
export function formatIndustry(raw: string | null | undefined): string {
  if (!raw) return '—';
  const trimmed = raw.trim();
  if (!trimmed) return '—';

  // Check if it's a pure numeric SIC code
  if (/^\d{4}$/.test(trimmed)) {
    return SIC_CODES[trimmed] ?? `SIC ${trimmed}`;
  }

  // Check if it's a comma-separated list of SIC codes
  if (/^\d{4}(,\s*\d{4})*$/.test(trimmed)) {
    const codes = trimmed.split(',').map((c) => c.trim());
    const first = SIC_CODES[codes[0]] ?? `SIC ${codes[0]}`;
    return codes.length > 1 ? `${first} (+${codes.length - 1})` : first;
  }

  // Already a human-readable name — pass through
  return trimmed;
}
