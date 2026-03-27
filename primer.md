# CirrusLabs Python Backend — Primer

> **This is the living memory of the project.** Read this before making any changes. Update it after every change.

---

## 1. Project Purpose

Python/FastAPI backend for CirrusLabs's signal-driven outbound campaign automation. This is the **API layer + async task execution** for the same system powered by the TypeScript frontend (separate repo). Both repos share the same Supabase database.

**Core loop:** Define ICP --> Detect signals --> Generate copy --> Find leads --> Send --> Measure --> Learn --> Repeat (better)

Expert knowledge lives in `.md` files under `context/`. The 6 skills read those files and adapt intelligently to each offer and campaign.

**Stack:** Python 3.13 · FastAPI · Celery + Redis · Supabase · Apollo.io · OpenAI
**GitHub:** https://github.com/ashirimi1019/Claude-GTM-Python
**Frontend (TS):** https://github.com/ashirimi1019/CirrusClaudebot

---

## 2. Architecture Summary

```
Frontend (Next.js)  ──HTTP──>  FastAPI  ──Redis pub/sub──>  SSE (real-time logs)
                                  │
                                  │ POST /api/skills/run
                                  v
                               Celery Worker  ──async_to_sync──>  Skill 1-6 (pure async)
                                  │
                                  │ via Redis broker
                                  v
                           Celery Beat (scheduler)
                                  │
                          ┌───────┴───────┐
                          │               │
                    Agent Pipeline    Health Monitor
                    (daily 9am)       (every 6 hours)
```

- **FastAPI** — Application factory (`app/main.py`), routes, SSE streaming, error handling
- **Celery** — Background task execution (skills, agents, health monitor, stale run cleanup)
- **Redis** — Celery broker/backend + pub/sub for SSE real-time streaming
- **Supabase** — Shared PostgreSQL database (11 migrations, RLS disabled)
- **Apollo.io** — Company search, contact enrichment, sequences, analytics
- **OpenAI** — Copy generation (gpt-4o), company classification, personalization, agent reasoning

All skills are **pure async functions** in `core/skills/`. Celery wraps them via `asgiref.async_to_sync` in `workers/skill_tasks.py`.

---

## 3. The 6 Skills

| Skill | API Call | Cost | Output |
|-------|----------|------|--------|
| 1 — New Offer | `POST /api/skills/run {skill_id: 1}` | Free | `offers/{slug}/positioning.md` + DB record |
| 2 — Campaign Strategy | `POST /api/skills/run {skill_id: 2}` | Free | `offers/{slug}/campaigns/{campaign}/strategy.md` + DB record |
| 3 — Campaign Copy | `POST /api/skills/run {skill_id: 3}` | ~$0.50 OpenAI | `copy/email-variants.md`, `linkedin-variants.md`, `personalization-notes.md` |
| 4 — Find Leads | `POST /api/skills/run {skill_id: 4}` | ~$2-5 Apollo | `leads/all_leads.csv` (company+contact per row) |
| 5 — Launch Outreach | `POST /api/skills/run {skill_id: 5}` | Free | Apollo sequences created; `outreach/messages.csv` |
| 6 — Campaign Review | `POST /api/skills/run {skill_id: 6}` | Free | `results/learnings.md` + updated `what-works.md` |

Skills 1-2 take a config dict. Skills 3-6 take `offer_slug` + `campaign_slug`. All dispatched via `run_skill_task.delay()` and executed in Celery workers.

### Skill Output Files

```python
SKILL_OUTPUTS = {
    1: ["positioning.md"],
    2: ["strategy.md"],
    3: ["copy/email-variants.md", "copy/linkedin-variants.md", "copy/personalization-notes.md"],
    4: ["leads/all_leads.csv"],
    5: ["outreach/messages.csv"],
    6: ["results/learnings.md"],
}
```

---

## 4. API Routes

### Health
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Returns `{"status": "ok"}` |

### Skills (`/api/skills`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/skills/run` | None | Queue skill via Celery; returns `task_id` |
| GET | `/api/skills/status` | None | Check filesystem for skill output files |
| GET | `/api/skills/run-summary` | None | Read `run-summary.json` from campaign leads dir |
| GET | `/api/skills/stream` | None | SSE stream of skill execution logs via Redis pub/sub |

### Offers (`/api/offers`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/offers` | None | List all offers (ordered by created_at desc) |
| GET | `/api/offers/{slug}` | None | Get a single offer by slug |
| POST | `/api/offers` | None | Create a new offer (auto-generates slug from name) |

### Campaigns (`/api/campaigns`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/campaigns` | None | List all campaigns (ordered by created_at desc) |
| GET | `/api/campaigns/{slug}` | None | Get a single campaign by slug |
| POST | `/api/campaigns` | None | Create campaign (looks up offer_id from offer_slug) |

### ICP (`/api`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/campaigns/{campaign_id}/icp-profile` | None | Return ICP profile for a campaign |
| POST | `/api/campaigns/{campaign_id}/icp-profile` | None | Save ICP profile (validates first via `validate_icp_profile`) |
| POST | `/api/icp/preview` | None | Preview ICP scoring results (dry run, max 500 companies) |

### Agents (`/api/agents`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/agents/run` | `X-Agent-Secret` | Launch agent pipeline via Celery |
| GET | `/api/agents/config` | `X-Agent-Secret` | Get autonomy config for a campaign (stub) |
| POST | `/api/agents/config` | `X-Agent-Secret` | Save agent config (stub) |
| GET | `/api/agents/approve` | `X-Agent-Secret` | List pending approval actions (stub) |
| POST | `/api/agents/approve` | `X-Agent-Secret` | Approve or reject an agent action (stub) |
| POST | `/api/agents/health` | `X-Agent-Secret` | Health monitor endpoint (stub) |

### Variants (`/api/variants`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/variants/pending` | None | List copy variants awaiting Tier 3 approval (stub) |
| POST | `/api/variants/{variant_id}/approve` | None | Approve or reject a flagged variant (stub) |

### Artifacts (`/api/artifacts`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/artifacts` | None | List all output files for an offer/campaign |
| GET | `/api/artifacts/{path}` | None | Read a specific artifact file (md, txt, csv, json) |

### Cron (`/api/cron`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/cron/cleanup-stale-runs` | `X-Agent-Secret` | Mark hung skill runs as failed |

---

## 5. Workers & Tasks

### Celery App (`workers/celery_app.py`)
- Broker + backend: Redis (`REDIS_URL`)
- Task serializer: JSON
- Time limits: 600s hard / 540s soft
- Timezone: UTC

### Beat Schedule
| Task Name | Schedule | Description |
|-----------|----------|-------------|
| `run_agent_cron` | Daily 9:00 UTC | Dispatch agent pipeline on all autonomous campaigns |
| `run_health_monitor` | Every 6 hours | Bounce rates, reply classification, enrollment batches |
| `cleanup_stale_runs` | Daily 3:00 UTC | Mark hung runs as failed (running >30min or queued >1hr) |

### Task Registry
| Task | File | Description |
|------|------|-------------|
| `run_skill` | `workers/skill_tasks.py` | Execute skill 1-6 via `_SKILL_REGISTRY` dispatch. Publishes SSE events. |
| `run_agent_pipeline` | `workers/agent_tasks.py` | Phase A (lead-quality) -> Phase B (icp-tuner -> copy-optimizer -> orchestrator) with conflict resolution |
| `run_agent_cron` | `workers/agent_tasks.py` | Daily cron: dispatch `run_agent_pipeline` on autonomous campaigns (TODO: wire to DB query) |
| `run_health_monitor` | `workers/scheduled_tasks.py` | Bounce circuit breaker, reply classification, enrollment batches (TODO: wire to real logic) |
| `cleanup_stale_runs` | `workers/scheduled_tasks.py` | Mark stale runs as failed (TODO: wire to Supabase query) |

---

## 6. Services Layer

### ICP Pipeline (`services/icp/` — 9 files)
The core scoring engine. Two-stage pipeline: Stage 1 (broad search) -> enrich -> Stage 2 (user strictness scoring).

| File | Purpose |
|------|---------|
| `types.py` | `IcpProfile`, `NormalizedIcpRules`, `IcpCompanyTrace`, `IcpFilterTrace`, `IcpScoringTrace`, `IcpConfidenceScore` |
| `constants.py` | `MAX_SCORE=215`, 8 dimension maxes, `STRICTNESS_BUNDLES` (4 levels), `SIZE_PRESETS`, `COMPETITOR_KEYWORDS`, `CONFIDENCE_FLOORS` |
| `normalizer.py` | `normalize_icp_profile()` — IcpProfile -> NormalizedIcpRules; `normalize_for_search_stage()` — broad rules for Stage 1 |
| `executor.py` | `execute_icp_pipeline()` — hard_filters -> scoring (8 dimensions) -> confidence_gate -> tiering |
| `validator.py` | `validate_icp_profile()` — validates structure, returns all errors (no short-circuit) |
| `resolver.py` | `resolve_execution_config()` — cascade: `campaign.icp_profile > offer.icp_profile > legacy scoring_config_overrides` |
| `preview.py` | `run_icp_preview()` — dry-run scoring for frontend ICP Builder UI |
| `migration.py` | `legacy_config_to_icp_profile()` — converts old scoring config to ICP profile format |
| `apollo_query.py` | Build Apollo search params from ICP profile |

**8 scoring dimensions:** hiring_signal (40), company_size (50), funding (30), revenue (20), tech_stack (45), industry (15), domain (15), intent (35) = 215 max

**Strictness levels:** broad (75 threshold), balanced (115), strict (165), very_strict (195)

### Scoring (`services/scoring.py`)
Legacy scoring used when ICP Builder profile is not set. Parses YAML blocks from vertical `scoring.md` files. Cascade: `campaign_overrides > offer_overrides > vertical scoring.md > DEFAULT_SCORING_CONFIG`.

### Geography (`services/geography.py`)
- **Single source of truth** for all country/state logic
- Default: Americas (US, CA, MX, BR, AR, CL, CO, PE, UY)
- Resolution: `campaign_countries ?? offer_countries ?? DEFAULT_ALLOWED_COUNTRIES`
- Runs **before** contact enrichment to save Apollo credits
- Rejected companies logged as `[GEOGRAPHY REJECT]`

### Deduplication (`services/deduplication.py`)
- `deduplicate_contacts()` — by email, merges missing fields from duplicates
- `deduplicate_companies()` — by apollo_id or domain, combines array fields
- `deduplicate_messages()` — by (campaign_id, contact_id, channel), keeps latest

### Enrollment Ramp (`services/enrollment_ramp.py`)
Gradual send volume increase: Day 1: 10%, Day 2: 25%, Day 3: 50%, Day 4+: max_daily (default 50). Always enrolls at least 1.

### Run Tracker (`services/run_tracker.py`)
`SkillRunTracker` publishes real-time SSE events via Redis pub/sub:
- Channel: `skill-run:{offer_slug}:{campaign_slug or 'none'}:{skill_id}`
- Methods: `log()`, `start_step()`, `complete_step()`, `fail_step()`, `finish()`
- Context manager support: `with SkillRunTracker(...) as tracker:`
- Uses sync `redis` (for Celery tasks); SSE subscriber uses `redis.asyncio`

### Rate Limiter (`services/rate_limiter.py`)
Stub — always returns True. Future: integrate with Redis sliding window.

### Logging (`services/logging.py`)
structlog configuration. JSON renderer in production, ConsoleRenderer when `LOG_LEVEL=debug`. Called once at app startup in lifespan.

### Other Services
| File | Purpose |
|------|---------|
| `services/personalization.py` | Contact-level personalization |
| `services/intelligence.py` | Company/contact intelligence classification |
| `services/csv_export.py` | CSV output for leads |
| `services/retry.py` | Retry utilities |

---

## 7. Agent System

### Architecture
4 domain-specific agents + 1 orchestrator, running as a staged Celery pipeline:

| Agent | ID | Domain | File | Purpose |
|-------|-----|--------|------|---------|
| Lead Quality | `lead-quality` | `lead` | `core/agents/lead_quality.py` | Detects false positives + missed opportunities |
| ICP Tuner | `icp-tuner` | `icp` | `core/agents/icp_tuner.py` | Suggests threshold/weight adjustments |
| Copy Optimizer | `copy-optimizer` | `copy` | `core/agents/copy_optimizer.py` | Analyzes variant performance, suggests copy changes |
| Orchestrator | `orchestrator` | `workflow` | `core/agents/orchestrator.py` | Reviews all results, plans skill dispatch order |

### Execution Pipeline
```
Phase A: Lead Quality (runs first, highest domain precedence)
    |
    v  build_prior_context()
Phase B: ICP Tuner -> Copy Optimizer -> Orchestrator
    |
    v  detect_conflicts()
Conflict Resolution (intra-agent dedup + cross-agent precedence)
    |
    v  execute_actions()
Auto-apply safe recommendations (risk_level == "safe")
```

### Conflict Resolution (`core/agents/conflict_detector.py`)
- **Intra-agent:** Only the highest-confidence recommendation per domain survives
- **Cross-agent:** Agent precedence determines winner on same domain
- Precedence: lead-quality (3) > icp-tuner (2) > copy-optimizer (1) > orchestrator (0)
- Outcomes: `apply`, `suppress`, `defer`

### Supporting Modules
| File | Purpose |
|------|---------|
| `types.py` | `RecommendationV2`, `AgentResultV2`, `PriorContext`, `ConflictResolution`, `HealthContext` |
| `context_builder.py` | `build_prior_context()` — builds PriorContext for downstream agents |
| `snapshot.py` | `build_snapshot()` — builds campaign state dict for agent reasoning (TODO: wire to Supabase) |
| `action_executor.py` | `execute_actions()` — auto-applies safe recommendations |
| `memory.py` | `save_agent_memory()` — persists learnings to JSON file (max 1000 entries, trims oldest) |
| `llm_reasoning.py` | `reason_about()` — all agent OpenAI calls go through here (gpt-4o, temp 0.3, json_object response) |

### Recommendation Types
```python
RecommendationV2(
    domain="icp|copy|lead|workflow",
    action="short description",
    params={},
    confidence=0.0-1.0,
    reasoning="why",
    risk_level="safe|moderate|risky",
)
```

### Guardrails (`core/guardrails/validators.py`)
3-tier anti-hallucination system:
- **Tier 2 (automated):** Body length <2000 chars, subject <200 chars, unfilled placeholders, hallucination markers ("as an ai", "based on my training")
- **Tier 3 (human approval):** Aggressive CTAs ("act now", "limited time"), competitor comparisons

---

## 8. Models (Pydantic v2)

All models in `models/`:

| Model | File | Key Fields |
|-------|------|------------|
| `Offer` / `OfferCreate` | `offer.py` | slug, title, description, default_vertical_id, status, allowed_countries/states, icp_profile |
| `Campaign` / `CampaignCreate` | `campaign.py` | offer_id, slug, title, vertical_id, status, icp_profile, scoring_config_overrides |
| `Company` | `company.py` | apollo_id, domain, employee_count, industry, funding_stage, tech_stack, icp_score/tier/confidence |
| `Contact` | `contact.py` | email (UNIQUE), title, seniority, department, email_status |
| `Evidence` | `evidence.py` | signal_type (6 types), signal_name, intensity, recency, source (5 sources) |
| `Message` / `MessageVariant` | `message.py` | channel (email/linkedin/sms), status (8 states), subject, body |
| `SequenceMetrics` / `CampaignMetrics` | `metrics.py` | sent, opened, clicked, replied, bounced + computed rates |

### API Schemas (`models/api.py`)
| Schema | Route |
|--------|-------|
| `RunSkillRequest` / `RunSkillResponse` | POST /api/skills/run |
| `SkillStatusResponse` | GET /api/skills/status |
| `IcpPreviewRequest` / `IcpPreviewResponse` | POST /api/icp/preview |
| `RunAgentsRequest` | POST /api/agents/run |
| `AgentConfigRequest` | POST /api/agents/config |
| `ApproveActionRequest` | POST /api/agents/approve |

### ICP Types (`services/icp/types.py`)
`IcpProfile`, `StrictnessConfig`, `HardFiltersConfig`, `CompanySizeFilter`, `TechMustHave`, `GeographyFilter`, `ScoringConfig`, `EnrichmentConfig`, `NormalizedIcpRules`, `IcpCompanyTrace`, `IcpFilterTrace`, `IcpScoringTrace`, `IcpConfidenceScore`, `IcpTwoStageTrace`

### Apollo Types (`clients/apollo/types.py`)
`ApolloCompany`, `ApolloContact`, `ApolloQueryParams`, `ApolloSearchResponse`, `ApolloOrgEnrichmentResult`

### Agent Types (`core/agents/types.py`)
`RecommendationV2`, `AgentResultV2`, `HealthContext`, `PriorContext`, `ConflictResolution`

---

## 9. Clients

| Client | File | Singleton | Purpose |
|--------|------|-----------|---------|
| Supabase (service-role) | `clients/supabase_client.py` | `@lru_cache` | Full read/write access |
| Supabase (anon) | `clients/supabase_client.py` | `@lru_cache` | Read-only (matches frontend) |
| OpenAI | `clients/openai_client.py` | `@lru_cache` | AsyncOpenAI — `generate_copy()`, `classify_company()`, `generate_personalization()` |

### Apollo Client (`clients/apollo/` — 8 files)

| File | Purpose |
|------|---------|
| `search.py` | `search_companies()` — POST /v1/mixed_companies/search with pagination + credit budget |
| `contacts.py` | Contact discovery + enrichment |
| `enrichment.py` | Organization enrichment by domain |
| `sequences.py` | Create, activate, enroll, pause sequences |
| `analytics.py` | Sequence analytics + contact activity log |
| `types.py` | `ApolloCompany`, `ApolloContact`, `ApolloQueryParams`, `ApolloSearchResponse`, `ApolloOrgEnrichmentResult` |
| `errors.py` | `ApolloError` (extends `AppError`) + `handle_apollo_error()` — maps HTTP codes to typed errors with retryable flag |
| `utils.py` | `normalize_domain()`, `api_headers()`, `APOLLO_BASE_URL` |

All Apollo requests use `httpx.AsyncClient` with 30s timeout. Rate limit (429) and server errors (5xx) are marked retryable.

---

## 10. Database Schema

**Supabase** — shared instance with the TypeScript frontend (11 migrations applied):

| Table | Purpose | Key Constraints |
|-------|---------|-----------------|
| `offers` | Offer definitions + positioning | `default_vertical_id` FK to verticals |
| `companies` | Discovered companies + ICP scores | |
| `evidence` | Hiring signals | FK to companies |
| `contacts` | Decision-makers | **UNIQUE on email** |
| `campaigns` | Strategies + status | `vertical_id` FK, `icp_profile` JSONB |
| `campaign_companies` | Company <-> campaign membership | |
| `message_variants` | Email/LinkedIn copy per campaign | |
| `messages` | Sent messages + tracking | |
| `tool_usage` | API cost tracking per call | |
| `skill_runs` | Skill execution history + SSE log lines | |
| `verticals` | 3 verticals: staffing, ai-data-consulting, cloud-software-delivery | |
| `company_intelligence` | OpenAI classification per company | |
| `contact_intelligence` | Contact-level segment assignment | |
| `segment_summaries` | Per-campaign segment rollups | |
| `campaign_sequences` | Apollo sequences | **UNIQUE(campaign_id, segment_key)** |

**RLS:** Disabled — anon key can read all tables.

---

## 11. Configuration

All settings loaded via `pydantic-settings` from `.env` file (`app/config.py`). Singleton via `@lru_cache`.

```bash
# Required — Core services
SUPABASE_URL=                      # Supabase project URL
SUPABASE_SERVICE_ROLE_KEY=         # Full access key (backend only)
APOLLO_API_KEY=                    # Apollo.io API key
OPENAI_API_KEY=                    # OpenAI API key

# Optional
SUPABASE_ANON_KEY=                 # Read-only key (matches frontend)

# Redis (Celery broker + SSE pub/sub)
REDIS_URL=redis://localhost:6379/0 # Default

# Agent system
AGENT_INTERNAL_SECRET=             # Required for /api/agents/* routes

# Feature flags
ICP_BUILDER_ENABLED=true           # Default: true (activate ICP v2 pipeline in Skill 4)

# Logging
LOG_LEVEL=info                     # debug | info | warning | error

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Directories
CONTEXT_DIR=context                # Expert knowledge .md files
OFFERS_DIR=offers                  # Per-offer output directory
```

---

## 12. Testing

**375 test functions** across 7 test directories. Framework: pytest + pytest-asyncio + pytest-httpx.

```bash
uv run pytest -v                           # All tests
uv run pytest tests/services/icp/ -v       # ICP tests only
uv run pytest --tb=short -q                # Quick summary
uv run coverage run -m pytest && uv run coverage report  # Coverage
```

### Test Structure
```
tests/
  conftest.py                    # Shared fixtures (auto-sets env vars, clears settings cache)
  test_enrollment_ramp.py        # Enrollment ramp day calculations
  test_guardrails.py             # Tier 2 + Tier 3 copy validation
  test_models.py                 # Pydantic model validation, slugify
  test_rate_limiter.py           # Rate limiter stub
  routes/
    test_health.py               # Health endpoint
    test_skills_api.py           # Skills run, status, stream
    test_offers_api.py           # Offers CRUD
    test_campaigns_api.py        # Campaigns CRUD
    test_icp_api.py              # ICP profile get/save/preview
    test_agents_api.py           # Agent routes + auth
    test_safety_routes.py        # Path traversal, error handling
  services/
    icp/
      test_constants.py          # ICP constants validation
      test_executor.py           # Hard filters, scoring, tiering
      test_normalizer.py         # Profile normalization, strictness
      test_preview.py            # Preview pipeline
      test_resolver.py           # Config resolution cascade
      test_validator.py          # Profile validation
      test_migration.py          # Legacy config migration
    test_geography.py            # Geography filtering + resolution
    test_deduplication.py        # Contact/company/message dedup
    test_scoring.py              # Legacy scoring config parsing
    test_verticals.py            # Vertical loader + resolver
    test_csv_export.py           # CSV export
    test_intelligence.py         # Classification
    test_personalization.py      # Personalization generation
    test_run_tracker.py          # SSE event publishing
  clients/
    test_apollo.py               # Apollo client (search, errors, types)
  agents/
    test_conflict_detector.py    # Intra/cross-agent conflict resolution
    test_context_builder.py      # Prior context building
    test_types.py                # Agent type validation
  skills/
    test_skill_1.py through test_skill_6.py  # Skill function tests
  workers/
    test_celery.py               # Celery app config + task registration
```

### Test Fixtures (`conftest.py`)
- `_set_test_env` (autouse) — sets all required env vars via monkeypatch
- Clears `get_settings.cache_clear()` between tests to prevent stale singletons
- `asyncio_mode = "auto"` in pyproject.toml — all async tests auto-detected

---

## 13. Known Patterns & Gotchas

### Celery + Async
- Skills are **pure async functions** — Celery wraps them via `asgiref.async_to_sync`
- Never call `asyncio.run()` inside a Celery task — use `async_to_sync(fn)(args)` instead
- Task time limit is 600s — long-running skills (especially Skill 4) can hit this
- `bind=True` on tasks gives access to `self.request.id` for task correlation
- SSE termination event sent in `skill_tasks.py` after skill completes (best-effort)

### Supabase (Python SDK)
- The Python Supabase client does NOT have `.single()` — use `.execute()` and check `result.data` length
- Empty result: `result.data` is `[]`, not an error — check with `if not result.data:`
- Unique constraint violations surface as exceptions with "duplicate" or "23505" in the string
- Two client singletons: `get_supabase_client()` (service role) and `get_supabase_anon_client()` (read-only)
- Both are `@lru_cache(maxsize=1)` — they persist for the app lifetime

### Pydantic v2
- All models use Pydantic v2 with `model_validate()` (not `parse_obj()`)
- snake_case fields with `alias` for camelCase DB JSONB compatibility
- `model_config = {"populate_by_name": True}` enables both field name and alias
- `Field(default_factory=dict)` for mutable defaults — never use `{}`
- `OfferCreate` / `CampaignCreate` auto-generate slug from name via `@model_validator(mode="after")`

### structlog
- All modules use `structlog.get_logger()` — NOT stdlib `logging`
- Structured key-value logging: `logger.info("message", key=value, key2=value2)`
- JSON renderer in production, ConsoleRenderer when `LOG_LEVEL=debug`
- `configure_logging()` called once at app startup in lifespan

### Error Handling
- `AppError(message, status_code, code)` — machine-readable `code` field for frontend
- `ApolloError` extends `AppError` with `retryable` flag and `apollo_code`
- Routes: `try: ... except AppError: raise except Exception as exc: raise to_app_error(exc)`
- `to_app_error()` passes through AppError, wraps everything else as 500
- Global exception handlers in `create_app()` catch unhandled errors
- Never swallow exceptions silently — at minimum `logger.warning`

### SSE Streaming
- Skill runs publish events to Redis pub/sub channels
- Channel format: `skill-run:{offer_slug}:{campaign_slug or 'none'}:{skill_id}`
- SSE timeout: 600 seconds (10 minutes)
- Termination: `{"type": "done"}` or `{"step": "done"}` event closes the stream
- Uses `redis.asyncio` for the subscriber (SSE endpoint) and sync `redis` for the publisher (Celery tasks)

### Path Traversal Protection
- All artifact/status routes resolve paths and check `path.is_relative_to(offers_root)` before reading
- Never construct file paths from user input without this check
- Applies to: `/api/skills/status`, `/api/skills/run-summary`, `/api/artifacts`, `/api/artifacts/{path}`

### Agent Security
- All `/api/agents/*` routes require `X-Agent-Secret` header (via `Depends(verify_agent_secret)`)
- Header validated against `agent_internal_secret` from config
- If `agent_internal_secret` is empty, returns 500 (not 403)

### Cost Optimization (Skill 4)
- Companies are **ICP-scored BEFORE contact enrichment** — below-threshold companies never enriched
- Geography rejection also runs before enrichment for the same reason
- Two-stage pipeline: Stage 1 (broad) -> enrich qualifying companies -> Stage 2 (strict scoring)

### ICP Builder Priority
- When `icp_profile != null`, it is the ABSOLUTE source of truth
- `scoring_config_overrides` is completely ignored when `icp_profile` is set
- Resolution: `campaign.icp_profile > offer.icp_profile > legacy scoring_config_overrides`

### Vertical System
- 3 verticals: staffing, ai-data-consulting, cloud-software-delivery
- 8 playbook `.md` files each under `context/verticals/{slug}/`
- Resolution: `campaign.vertical_id ?? offer.default_vertical_id`
- Services in `services/verticals/` (types, loader, resolver, context_builder)

---

## 14. Code Review History

6 review passes completed, 70+ findings fixed across all severity levels:

| Pass | Commit | Focus |
|------|--------|-------|
| 1 | `8cc3b0c` | Initial code review issues — 375 tests passing |
| 2 | `3228864` | 17 fixes across high/medium/low severity |
| 3 | `a1d1946` | 16 fixes (1 critical) |
| 4 | `0c073ba` | All pass 4 findings + comprehensive CLAUDE.md |
| 5 | `36b3234` | Ruff clean, zero warnings |

All tests passing. `ruff check .` clean. `mypy .` strict mode enabled.

---

## 15. Change History

### Build History (chronological)
| Commit | Description |
|--------|-------------|
| `163cb96` | Initial scaffold — FastAPI + Pydantic + 58 tests |
| `49df574` | Services, clients, ICP pipeline — 204 tests |
| `1bac23f` | Complete backend — ICP pipeline, Celery workers, API routes, SSE — 293 tests |
| `ea1118b` | Skills 1-6, AI agent system, safety routes — 323 tests |
| `e995228` | Wire Celery tasks to real skill/agent implementations — 325 tests |
| `9add08e` | Upgrade to Python 3.13 (latest stable) |
| `8cc3b0c` | Code review pass 1 — 375 tests passing |
| `3228864` | Code review pass 2 — 17 fixes |
| `a1d1946` | Code review pass 3 — 16 fixes (1 critical) |
| `0c073ba` | Code review pass 4 + comprehensive CLAUDE.md |
| `36b3234` | Code review pass 5 — ruff clean, zero warnings |

---

## 16. Current Status

### What's Working
- FastAPI application factory with full route registration
- All 10 route groups with proper error handling and path traversal protection
- 6 skill implementations as pure async functions
- Celery task dispatch with SSE real-time streaming via Redis pub/sub
- ICP pipeline (normalizer -> executor -> resolver -> preview -> validator -> migration)
- 4-agent system with staged execution, conflict detection, context passing
- 3-tier guardrails (automated + human approval)
- Geography filtering, deduplication, enrollment ramp
- Apollo client (8 files — search, contacts, enrichment, sequences, analytics, errors)
- OpenAI client (copy generation, classification, personalization)
- 375 tests passing, ruff clean, mypy strict
- Comprehensive CLAUDE.md

### What Needs Wiring
Several components have stub implementations that need to be connected to real logic:
- `workers/scheduled_tasks.py` — `run_health_monitor()` and `cleanup_stale_runs()` have TODO stubs
- `workers/agent_tasks.py` — `run_agent_cron()` needs to query autonomous campaigns
- `core/agents/snapshot.py` — `build_snapshot()` returns stub data (needs Supabase queries)
- `app/routes/variants.py` — `list_pending_variants()` and `approve_variant()` are stubs
- `app/routes/agents.py` — `get_agent_config()`, `save_agent_config()`, `list_pending_approvals()` return stub data
- `services/rate_limiter.py` — always returns True (needs Redis sliding window)

---

## 17. Open Items

### High Priority
- [ ] Wire `build_snapshot()` to real Supabase queries (agents need real campaign data)
- [ ] Wire `run_health_monitor()` to real sequence analytics + bounce circuit breaker
- [ ] Wire `cleanup_stale_runs()` to Supabase query for stale skill_runs
- [ ] Wire `run_agent_cron()` to query campaigns with `autonomy_level = 'autonomous'`

### Medium Priority
- [ ] Wire variant approval routes to Supabase `message_variants` table
- [ ] Wire agent config routes to `campaign_agent_config` table
- [ ] Implement real rate limiter with Redis sliding window
- [ ] Add authentication/authorization beyond `X-Agent-Secret`

### Low Priority / Future
- [ ] Frontend geography UI (set overrides directly in Supabase for now)
- [ ] Agent memory retrieval (currently write-only via `save_agent_memory()`)
- [ ] Enrollment ramp integration with health monitor batches
- [ ] Cost tracking integration with `tool_usage` table

---

## Development Commands

```bash
# Install dependencies
uv sync && uv sync --group dev

# Start Redis (required for Celery + SSE)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start API server
uv run uvicorn app.main:create_app --factory --reload --port 8000

# Start Celery worker
uv run celery -A workers.celery_app worker --loglevel=info

# Start Celery Beat (scheduled tasks)
uv run celery -A workers.celery_app beat --loglevel=info

# Run tests
uv run pytest -v                           # All tests
uv run pytest tests/services/icp/ -v       # ICP tests only
uv run pytest --tb=short -q                # Quick summary

# Lint + type check — MUST pass before committing
uv run ruff check .                        # Lint (ruff)
uv run mypy .                              # Type check (strict mode)

# Coverage
uv run coverage run -m pytest && uv run coverage report
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API server won't start | Check `.env` exists with all required keys |
| Skill runs stay "queued" | Redis not running — `docker run -d --name redis -p 6379:6379 redis:7-alpine` |
| Celery worker won't connect | Check `REDIS_URL` in .env; verify Redis is reachable |
| SSE stream never receives events | Celery worker not running — skills execute in worker, not API server |
| Agent routes return 403 | `X-Agent-Secret` header doesn't match `AGENT_INTERNAL_SECRET` |
| Agent routes return 500 | `AGENT_INTERNAL_SECRET` is empty — set it in .env |
| Skill 4 returns 0 results | Geography filter excluding all companies — check `[GEOGRAPHY REJECT]` logs |
| Skill 4 timeout | Task time limit is 600s — reduce scope or increase limit |
| Database errors | Ensure all 11 migrations are applied in Supabase |
| Import errors | Run `uv sync` to install dependencies |
| Tests fail with connection errors | Tests mock all external services via `conftest.py` fixtures |
| ICP Builder not activating | Set `ICP_BUILDER_ENABLED=true`; ensure campaign has `icp_profile` saved |

---

## File Organization

```
├── app/                          <-- FastAPI application
│   ├── main.py                   Application factory (create_app)
│   ├── config.py                 Settings via pydantic-settings (.env)
│   ├── errors.py                 AppError, to_app_error, error_response
│   ├── sse.py                    SSE streaming via Redis pub/sub + sse-starlette
│   └── routes/
│       ├── health.py             GET /health
│       ├── skills.py             POST /run, GET /status, GET /run-summary, GET /stream
│       ├── offers.py             GET/POST /api/offers
│       ├── campaigns.py          GET/POST /api/campaigns
│       ├── icp.py                GET/POST icp-profile, POST /icp/preview
│       ├── agents.py             POST /run, GET/POST /config, GET/POST /approve
│       ├── health_monitor.py     POST /api/agents/health
│       ├── variants.py           GET /pending, POST /{id}/approve
│       ├── artifacts.py          GET list/read skill output files
│       └── cron.py               POST /cleanup-stale-runs
│
├── core/
│   ├── skills/                   Skill 1-6 (pure async functions)
│   ├── agents/                   4 agents + orchestrator (11 files)
│   └── guardrails/               Tier 2 + Tier 3 copy validators
│
├── clients/
│   ├── supabase_client.py        Service-role + anon-key singletons
│   ├── openai_client.py          AsyncOpenAI — copy, classification, personalization
│   └── apollo/                   8-file module
│
├── services/
│   ├── icp/                      ICP pipeline (9 files)
│   ├── verticals/                Vertical system (4 files)
│   ├── geography.py              Geography filtering — single source of truth
│   ├── scoring.py                Legacy scoring
│   ├── deduplication.py          Contact/company/message dedup
│   ├── enrollment_ramp.py        Gradual batch size ramp
│   ├── run_tracker.py            SSE events via Redis pub/sub
│   ├── rate_limiter.py           Stub — always allows
│   ├── logging.py                structlog configuration
│   ├── personalization.py        Contact personalization
│   ├── intelligence.py           Classification
│   ├── csv_export.py             CSV output
│   └── retry.py                  Retry utilities
│
├── models/                       Pydantic v2 domain models (7 files)
├── workers/                      Celery tasks (4 files)
├── tests/                        pytest suite (375 tests)
├── context/                      Expert knowledge (.md files)
├── offers/                       Per-offer + per-campaign outputs
├── pyproject.toml                Dependencies, ruff, mypy, pytest config
├── .env                          Copy from .env.example
├── CLAUDE.md                     Project instructions
└── primer.md                     Living project memory (this file)
```
