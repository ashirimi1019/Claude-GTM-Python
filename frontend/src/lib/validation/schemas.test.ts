import { describe, it, expect } from 'vitest';
import { slugSchema, skillIdSchema, RunSkillSchema, StatusQuerySchema } from '@/lib/validation/schemas';

// ── slugSchema ───────────────────────────────────────────────────────────────

describe('slugSchema', () => {
  it('accepts a valid slug', () => {
    expect(slugSchema.safeParse('talent-as-service-us').success).toBe(true);
  });

  it('accepts slug with numbers', () => {
    expect(slugSchema.safeParse('campaign-2026').success).toBe(true);
  });

  it('rejects empty string', () => {
    const result = slugSchema.safeParse('');
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('Required');
    }
  });

  it('rejects slug with spaces', () => {
    expect(slugSchema.safeParse('talent as service').success).toBe(false);
  });

  it('rejects slug with uppercase letters', () => {
    expect(slugSchema.safeParse('Talent-As-Service').success).toBe(false);
  });

  it('rejects slug with special characters', () => {
    expect(slugSchema.safeParse('campaign_2026').success).toBe(false);
    expect(slugSchema.safeParse('campaign.2026').success).toBe(false);
  });

  it('rejects slug over 100 characters', () => {
    const long = 'a'.repeat(101);
    const result = slugSchema.safeParse(long);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('Too long');
    }
  });
});

// ── skillIdSchema ────────────────────────────────────────────────────────────

describe('skillIdSchema', () => {
  it('accepts skill IDs 1 through 6', () => {
    for (const id of [1, 2, 3, 4, 5, 6]) {
      expect(skillIdSchema.safeParse(id).success).toBe(true);
    }
  });

  it('coerces string "3" to number 3', () => {
    const result = skillIdSchema.safeParse('3');
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data).toBe(3);
    }
  });

  it('rejects 0 (below range)', () => {
    const result = skillIdSchema.safeParse(0);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('Skill ID must be 1–6');
    }
  });

  it('rejects 7 (above range)', () => {
    const result = skillIdSchema.safeParse(7);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].message).toBe('Skill ID must be 1–6');
    }
  });

  it('rejects non-numeric string', () => {
    expect(skillIdSchema.safeParse('not-a-skill').success).toBe(false);
    expect(skillIdSchema.safeParse('skill-1').success).toBe(false);
  });

  it('rejects float', () => {
    expect(skillIdSchema.safeParse(1.5).success).toBe(false);
  });
});

// ── RunSkillSchema ───────────────────────────────────────────────────────────

describe('RunSkillSchema', () => {
  it('accepts skill-1 with offer only', () => {
    expect(RunSkillSchema.safeParse({ skillId: 1, offer: 'talent-as-service-us' }).success).toBe(true);
  });

  it('accepts skill-1 with offer and campaign', () => {
    expect(
      RunSkillSchema.safeParse({
        skillId: 1,
        offer: 'talent-as-service-us',
        campaign: 'hiring-data-engineers-q1',
      }).success
    ).toBe(true);
  });

  it('accepts skill-2 with offer only', () => {
    expect(RunSkillSchema.safeParse({ skillId: 2, offer: 'talent-as-service-us' }).success).toBe(true);
  });

  it('accepts skill-3 with both offer and campaign', () => {
    expect(
      RunSkillSchema.safeParse({
        skillId: 3,
        offer: 'talent-as-service-us',
        campaign: 'hiring-data-engineers-q1',
      }).success
    ).toBe(true);
  });

  it('rejects skill-3 missing campaign', () => {
    const result = RunSkillSchema.safeParse({ skillId: 3, offer: 'talent-as-service-us' });
    expect(result.success).toBe(false);
  });

  it('rejects skill-4 missing campaign', () => {
    expect(RunSkillSchema.safeParse({ skillId: 4, offer: 'talent-as-service-us' }).success).toBe(false);
  });

  it('rejects skill-5 missing campaign', () => {
    expect(RunSkillSchema.safeParse({ skillId: 5, offer: 'talent-as-service-us' }).success).toBe(false);
  });

  it('rejects skill-6 missing campaign', () => {
    expect(RunSkillSchema.safeParse({ skillId: 6, offer: 'talent-as-service-us' }).success).toBe(false);
  });

  it('rejects invalid skillId 7', () => {
    expect(
      RunSkillSchema.safeParse({
        skillId: 7,
        offer: 'talent-as-service-us',
        campaign: 'hiring-data-engineers-q1',
      }).success
    ).toBe(false);
  });

  it('rejects invalid offer slug (has uppercase)', () => {
    expect(
      RunSkillSchema.safeParse({
        skillId: 1,
        offer: 'Talent-As-Service',
      }).success
    ).toBe(false);
  });

  it('rejects missing offer for skill 2+', () => {
    // Skill 1 has offer optional; skill 2+ requires it
    expect(
      RunSkillSchema.safeParse({
        skillId: 3,
        campaign: 'hiring-data-engineers-q1',
      }).success
    ).toBe(false);
  });

  it('accepts all skills 3-6 when both fields are valid', () => {
    for (const skillId of [3, 4, 5, 6] as const) {
      expect(
        RunSkillSchema.safeParse({
          skillId,
          offer: 'talent-as-service-us',
          campaign: 'hiring-data-engineers-q1',
        }).success
      ).toBe(true);
    }
  });
});

// ── StatusQuerySchema ────────────────────────────────────────────────────────

describe('StatusQuerySchema', () => {
  it('accepts offer only', () => {
    expect(StatusQuerySchema.safeParse({ offer: 'talent-as-service-us' }).success).toBe(true);
  });

  it('accepts offer + campaign', () => {
    expect(
      StatusQuerySchema.safeParse({
        offer: 'talent-as-service-us',
        campaign: 'hiring-data-engineers-q1',
      }).success
    ).toBe(true);
  });

  it('rejects missing offer', () => {
    expect(StatusQuerySchema.safeParse({}).success).toBe(false);
  });

  it('rejects invalid offer slug', () => {
    expect(StatusQuerySchema.safeParse({ offer: 'Invalid Offer' }).success).toBe(false);
  });
});
