/**
 * Shared Zod primitives for API route validation.
 *
 * Convention:
 *   - Use z.coerce.number() for values that may arrive as strings (query params)
 *   - Use z.number() for JSON body values where the frontend sends proper types
 *   - campaign is skill-aware: required for skills 3-6, optional for 1-2
 *
 * Note: the run route uses query params `skill`, `offer`, `campaign`
 * and the status route uses `offer`, `campaign` (no skillId needed for status).
 */
import { z } from 'zod';

// ── Primitives ──────────────────────────────────────────────────────────────

export const slugSchema = z
  .string()
  .min(1, 'Required')
  .max(100, 'Too long')
  .regex(/^[a-z0-9-]+$/, 'Must be lowercase letters, numbers, and hyphens only');

export const skillIdSchema = z.coerce
  .number()
  .int()
  .min(1, 'Skill ID must be 1–6')
  .max(6, 'Skill ID must be 1–6');

// ── Run skill — discriminated union on skillId ──────────────────────────────
// Skills 1–2: campaign optional; Skills 3–6: campaign required

export const RunSkillSchema = z.discriminatedUnion('skillId', [
  z.object({ skillId: z.literal(1), offer: slugSchema.optional(), campaign: slugSchema.optional() }),
  z.object({ skillId: z.literal(2), offer: slugSchema, campaign: slugSchema.optional() }),
  z.object({ skillId: z.literal(3), offer: slugSchema, campaign: slugSchema }),
  z.object({ skillId: z.literal(4), offer: slugSchema, campaign: slugSchema }),
  z.object({ skillId: z.literal(5), offer: slugSchema, campaign: slugSchema }),
  z.object({ skillId: z.literal(6), offer: slugSchema, campaign: slugSchema }),
]);

// ── Status query params ─────────────────────────────────────────────────────

export const StatusQuerySchema = z.object({
  offer: slugSchema,
  campaign: slugSchema.optional(),
});

// Type helpers
export type RunSkillInput = z.infer<typeof RunSkillSchema>;
export type StatusQueryInput = z.infer<typeof StatusQuerySchema>;
