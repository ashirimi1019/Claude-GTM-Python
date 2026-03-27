# CirrusLabs Python Backend — Signal-Driven Outbound Automation

**Stack:** Python 3.13 · FastAPI · Celery + Redis · Supabase · Apollo.io · OpenAI
**GitHub:** https://github.com/ashirimi1019/Claude-GTM-Python

---

## primer.md — Read This First

> **`primer.md` is the living memory of this project.** Read it before making any changes. Update it after every change.

**Rules:**
1. **Read `primer.md` before any changes** — latest architecture, vertical status, known limitations, change history
2. **Update `primer.md` after every change** — code, schema, config, API routes, workers, prompts
3. `primer.md` supersedes all other docs when there's a conflict

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep the main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `primer.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review `primer.md` at session start before making any changes
- After completing any task, silently update `primer.md` with: what was completed, exact next step, open blockers — this ensures state survives abrupt exits or context compaction

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run `uv run ruff check .`, `uv run mypy .`, `uv run pytest -v` — all must pass before committing
- Before closing or when asked to stop: check for uncommitted changes and remind the user to commit

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing issues without being told how

### 7. Context Window Management
- When the conversation reaches ~70% of the context window, proactively rewrite `primer.md` with current state before compaction
- If a session is resumed from compaction, read `primer.md` first — it has the latest state
- Flag anything uncertain with [UNCLEAR] rather than guessing

---

## System Overview

Signal-driven outbound campaign automation for CirrusLabs's staffing/consulting business.

**Core loop:** Define ICP --> Detect signals --> Generate copy --> Find leads --> Send --> Measure --> Learn --> Repeat (better)

Expert knowledge lives in `.md` files under `context/`. The 6 skills read those files and adapt intelligently to each offer and campaign.

This is the **Python/FastAPI backend** that provides the API layer + async task execution for the same system. The Next.js frontend (in the TypeScript repo) calls these API routes. Both repos share the same Supabase database.

---

## The 6 Skills

| Skill | API Call | Cost | Output |
|-------|----------|------|--------|
| 1 — New Offer | `POST /api/skills/run {skill_id: 1}` | Free | `offers/{slug}/positioning.md` + DB record |
| 2 — Campaign Strategy | `POST /api/skills/run {skill_id: 2}` | Free | `offers/{slug}/campaigns/{campaign}/strategy.md` + DB record |
| 3 — Campaign Copy | `POST /api/skills/run {skill_id: 3}` | ~$0.50 OpenAI | `copy/email-variants.md`, `linkedin-variants.md`, `personalization-notes.md` |
| 4 — Find Leads | `POST /api/skills/run {skill_id: 4}` | ~$2-5 Apollo | `leads/all_leads.csv` (company+contact per row) |
| 5 — Launch Outreach | `POST /api/skills/run {skill_id: 5}` | Free | Apollo sequences created; `outreach/messages.csv` |
| 6 — Campaign Review | `POST /api/skills/run {skill_id: 6}` | Free | `results/learnings.md` + updated `what-works.md` |

Skills are **pure async functions** in `core/skills/`. Celery wraps them via `asgiref.async_to_sync` in `workers/skill_tasks.py`.

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

## Database Schema

**Supabase** — shared instance with the TypeScript frontend (11 migrations applied):

| Table | Purpose |
|-------|---------|
| `offers` | Offer definitions + positioning; `default_vertical_id` FK, `allowed_countries/states` |
| `companies` | Discovered companies + ICP scores |
| `evidence` | Hiring signals |
| `contacts` | Decision-makers — UNIQUE on email |
| `campaigns` | Strategies + status; `vertical_id` FK, `allowed_countries/states`, `icp_profile` JSONB |
| `campaign_companies` | Company <-> campaign membership |
| `message_variants` | Email/LinkedIn copy per campaign |
| `messages` | Sent messages + tracking |
| `tool_usage` | API cost tracking per call |
| `skill_runs` | Skill execution history + SSE log lines |
| `verticals` | 3 verticals: staffing, ai-data-consulting, cloud-software-delivery |
| `company_intelligence` | OpenAI classification per company |
| `contact_intelligence` | Contact-level segment assignment |
| `segment_summaries` | Per-campaign segment rollups |
| `campaign_sequences` | Apollo sequences — UNIQUE(campaign_id, segment_key) |

**RLS:** Disabled — anon key can read all tables.

---

## Context Files (Your Expertise)

All skills read from `context/`:

```
context/
  frameworks/      icp-framework.md, positioning-canvas.md, signal-generation-guide.md,
                   signal-brainstorming-template.md, contact-finding-guide.md
  copywriting/     email-principles.md, linkedin-principles.md
  principles/      permissionless-value.md, use-case-driven.md, mistakes-to-avoid.md
  api-guides/      apollo-capabilities-guide.md, apollo-api-guide.md, openai-api-guide.md, supabase-guide.md
  learnings/       what-works.md  <-- grows with each campaign
  verticals/       staffing/, ai-data-consulting/, cloud-software-delivery/  (8 .md files each)
```

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
│       ├── skills.py             POST /api/skills/run, GET /api/skills/status, GET /api/skills/stream (SSE)
│       ├── offers.py             GET/POST /api/offers
│       ├── campaigns.py          GET/POST /api/campaigns
│       ├── icp.py                GET/POST /api/campaigns/{id}/icp-profile, POST /api/icp/preview
│       ├── agents.py             POST /api/agents/run, GET/POST /api/agents/config, GET/POST /api/agents/approve
│       ├── health_monitor.py     POST /api/agents/health (bounce circuit breaker)
│       ├── variants.py           GET /api/variants/pending, POST /api/variants/{id}/approve
│       ├── artifacts.py          GET /api/artifacts (list/read skill output files)
│       └── cron.py               POST /api/cron/cleanup-stale-runs
│
├── core/
│   ├── skills/                   Skill 1-6 implementations (pure async functions)
│   │   ├── skill_1_new_offer.py
│   │   ├── skill_2_campaign_strategy.py
│   │   ├── skill_3_campaign_copy.py
│   │   ├── skill_4_find_leads.py
│   │   ├── skill_5_launch_outreach.py
│   │   └── skill_6_campaign_review.py
│   ├── agents/                   Multi-agent system (4 agents + orchestrator)
│   │   ├── types.py              RecommendationV2, AgentResultV2, PriorContext, ConflictResolution
│   │   ├── orchestrator.py       Reviews all agent results, plans skill dispatch order
│   │   ├── lead_quality.py       Detects false positives + missed opportunities
│   │   ├── icp_tuner.py          Suggests threshold/weight adjustments
│   │   ├── copy_optimizer.py     Analyzes copy performance, suggests changes
│   │   ├── conflict_detector.py  Resolves domain conflicts between agents
│   │   ├── context_builder.py    Builds PriorContext for downstream agents
│   │   ├── snapshot.py           Builds campaign snapshot for agent reasoning
│   │   ├── action_executor.py    Auto-applies safe recommendations
│   │   ├── memory.py             Persists agent memory across runs
│   │   └── llm_reasoning.py      All agent OpenAI calls go through here
│   └── guardrails/
│       └── validators.py         Tier 2 (automated) + Tier 3 (human approval) copy checks
│
├── clients/
│   ├── supabase_client.py        Service-role + anon-key clients (lru_cache singletons)
│   ├── openai_client.py          AsyncOpenAI — copy generation, classification, personalization
│   └── apollo/                   8-file module
│       ├── search.py             Company search
│       ├── contacts.py           Contact discovery + enrichment
│       ├── enrichment.py         Organization enrichment by domain
│       ├── sequences.py          Create, activate, enroll, pause sequences
│       ├── analytics.py          Sequence analytics + contact activity log
│       ├── types.py              ApolloCompany, ApolloContact, ApolloQueryParams, etc.
│       ├── errors.py             ApolloError + handler
│       └── utils.py              normalize_domain
│
├── services/
│   ├── icp/                      ICP pipeline (7 files)
│   │   ├── constants.py          MAX_SCORE, STRICTNESS_BUNDLES, SIZE_PRESETS, etc.
│   │   ├── types.py              IcpProfile, NormalizedIcpRules, IcpCompanyTrace, etc.
│   │   ├── normalizer.py         normalize_icp_profile, normalize_for_search_stage
│   │   ├── executor.py           execute_icp_pipeline, evaluate_hard_filters, score_company_icp
│   │   ├── validator.py          validate_icp_profile
│   │   ├── resolver.py           Resolve effective ICP config from cascade
│   │   ├── preview.py            run_icp_preview (dry-run scoring)
│   │   ├── migration.py          migrate_icp_profile, legacy_config_to_icp_profile
│   │   └── apollo_query.py       Build Apollo search params from ICP profile
│   ├── verticals/                Vertical system (4 files)
│   │   ├── types.py              VerticalConfig, VerticalPlaybook
│   │   ├── loader.py             Load vertical .md files from disk
│   │   ├── resolver.py           Resolve vertical from campaign/offer cascade
│   │   └── context_builder.py    Build skill context with vertical content appended
│   ├── geography.py              Geography filtering — single source of truth
│   ├── scoring.py                Legacy scoring (when ICP Builder not set)
│   ├── deduplication.py          Contacts by email, companies by apollo_id/domain, messages
│   ├── personalization.py        Contact-level personalization
│   ├── intelligence.py           Company/contact intelligence classification
│   ├── csv_export.py             CSV output for leads
│   ├── enrollment_ramp.py        Gradual batch size increase (10% -> 25% -> 50% -> max)
│   ├── rate_limiter.py           API rate limiting (stub — always allows)
│   ├── run_tracker.py            SkillRunTracker — SSE events via Redis pub/sub
│   ├── retry.py                  Retry utilities
│   └── logging.py                structlog configuration
│
├── models/                       Pydantic v2 domain models
│   ├── offer.py                  Offer, OfferCreate
│   ├── campaign.py               Campaign, CampaignCreate
│   ├── company.py                Company
│   ├── contact.py                Contact
│   ├── evidence.py               Evidence (hiring signals)
│   ├── message.py                Message, MessageVariant
│   ├── metrics.py                CampaignMetrics
│   └── api.py                    RunSkillRequest/Response, IcpPreviewRequest/Response, agent schemas
│
├── workers/                      Celery tasks
│   ├── celery_app.py             App factory + Beat schedule
│   ├── skill_tasks.py            run_skill_task (dispatches to skill 1-6 functions)
│   ├── agent_tasks.py            run_agent_pipeline, run_agent_cron
│   └── scheduled_tasks.py        run_health_monitor, cleanup_stale_runs
│
├── tests/                        pytest test suite
│   ├── conftest.py               Shared fixtures
│   ├── test_enrollment_ramp.py
│   ├── test_guardrails.py
│   ├── test_models.py
│   ├── test_rate_limiter.py
│   ├── routes/                   Route tests
│   ├── services/                 Service tests (incl. services/icp/)
│   ├── clients/                  Client tests
│   ├── skills/                   Skill tests
│   ├── agents/                   Agent tests
│   └── workers/                  Worker tests
│
├── context/                      Expert knowledge (.md files — edit to tune the system)
├── offers/                       Per-offer + per-campaign outputs
├── pyproject.toml                Dependencies, ruff, mypy, pytest config
├── .env                          Copy from .env.example
└── primer.md                     Living project memory (authoritative)
```

---

## API Routes

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Simple health check — returns `{"status": "ok"}` |

### Skills (`/api/skills`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/skills/run` | Queue a skill run via Celery; returns `task_id` |
| GET | `/api/skills/status` | Check filesystem for skill output files |
| GET | `/api/skills/run-summary` | Read `run-summary.json` from campaign leads dir |
| GET | `/api/skills/stream` | SSE stream of skill execution logs via Redis pub/sub |

### Offers (`/api/offers`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/offers` | List all offers (ordered by created_at desc) |
| GET | `/api/offers/{slug}` | Get a single offer by slug |
| POST | `/api/offers` | Create a new offer |

### Campaigns (`/api/campaigns`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/campaigns` | List all campaigns (ordered by created_at desc) |
| GET | `/api/campaigns/{slug}` | Get a single campaign by slug |
| POST | `/api/campaigns` | Create a new campaign (looks up offer_id from offer_slug) |

### ICP (`/api`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/campaigns/{campaign_id}/icp-profile` | Return ICP profile for a campaign |
| POST | `/api/campaigns/{campaign_id}/icp-profile` | Save ICP profile (validates first) |
| POST | `/api/icp/preview` | Preview ICP scoring results (dry run, max 500 companies) |

### Agents (`/api/agents`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agents/run` | Launch agent pipeline via Celery (requires `X-Agent-Secret` header) |
| GET | `/api/agents/config` | Get autonomy config for a campaign |
| POST | `/api/agents/config` | Save agent config |
| GET | `/api/agents/approve` | List pending approval actions |
| POST | `/api/agents/approve` | Approve or reject an agent action |
| POST | `/api/agents/health` | Health monitor — bounce circuit breaker, reply classification |

### Variants (`/api/variants`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/variants/pending` | List copy variants awaiting Tier 3 approval |
| POST | `/api/variants/{variant_id}/approve` | Approve or reject a flagged copy variant |

### Artifacts (`/api/artifacts`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/artifacts` | List all output files for an offer/campaign |
| GET | `/api/artifacts/{path}` | Read a specific artifact file (md, txt, csv, json) |

### Cron (`/api/cron`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cron/cleanup-stale-runs` | Mark hung skill runs as failed (requires `X-Agent-Secret`) |

---

## Workers (Celery Tasks)

### Celery App (`workers/celery_app.py`)
- Broker + backend: Redis
- Task serializer: JSON
- Time limit: 600s hard / 540s soft
- All tasks are plain functions wrapping async code via `async_to_sync`

### Skill Tasks (`workers/skill_tasks.py`)
| Task Name | Description |
|-----------|-------------|
| `run_skill` | Execute any skill (1-6) as a background task. Skills 1-2 take config dict, skills 3-6 take offer_slug + campaign_slug. Publishes SSE events via `SkillRunTracker`. |

### Agent Tasks (`workers/agent_tasks.py`)
| Task Name | Description |
|-----------|-------------|
| `run_agent_pipeline` | Full staged pipeline: Phase A (lead-quality) -> Phase B (icp-tuner -> copy-optimizer -> orchestrator) with conflict resolution + auto-apply safe actions |
| `run_agent_cron` | Daily 9am UTC: dispatch agent pipeline on all autonomous campaigns |

### Scheduled Tasks (`workers/scheduled_tasks.py`)
| Task Name | Schedule | Description |
|-----------|----------|-------------|
| `run_health_monitor` | Every 6 hours | Check bounce rates, auto-pause >5% sequences, classify replies, process enrollment batches |
| `cleanup_stale_runs` | Daily 3am UTC | Mark hung runs as failed (running >30min or queued >1hr) |

---

## Services

### ICP Pipeline (`services/icp/`)
The ICP (Ideal Customer Profile) pipeline is the core scoring engine:
- **normalizer** — Converts raw ICP profile to normalized rules for scoring
- **executor** — `execute_icp_pipeline()`: normalizer -> hard filters -> scoring -> confidence gate -> tiering -> enrichment
- **validator** — Validates ICP profile structure and field constraints
- **resolver** — Resolves effective ICP config from cascade: `campaign.icp_profile > offer.icp_profile > legacy scoring_config_overrides`
- **preview** — Dry-run scoring for the frontend ICP Builder
- **migration** — `legacy_config_to_icp_profile()` converts old scoring config to new ICP profile format
- **apollo_query** — Build Apollo search params from ICP profile
- **Two-stage pipeline:** Stage 1 (broad search) -> enrich -> Stage 2 (user strictness scoring)

### Scoring (`services/scoring.py`)
Legacy scoring used when ICP Builder profile is not set:
- Parses scoring config from vertical `scoring.md` YAML blocks
- Cascade: `campaign_overrides > offer_overrides > vertical scoring.md > DEFAULT_SCORING_CONFIG`
- Default threshold: 75 points

### Geography (`services/geography.py`)
- **Single source of truth** — all geography logic lives here
- Default scope: **Americas** (US, Canada, Mexico, Brazil, Argentina, Chile, Colombia, Peru, Uruguay)
- Resolution: `campaign_countries ?? offer_countries ?? DEFAULT_ALLOWED_COUNTRIES`
- Runs **before** contact enrichment to save Apollo credits
- Rejected companies logged as `[GEOGRAPHY REJECT]`

### Deduplication (`services/deduplication.py`)
- `deduplicate_contacts()` — by email, merges missing fields from duplicates
- `deduplicate_companies()` — by apollo_id or domain, combines array fields
- `deduplicate_messages()` — by (campaign_id, contact_id, channel), keeps latest

### Enrollment Ramp (`services/enrollment_ramp.py`)
Gradual send volume increase:
- Day 1: 10% of total
- Day 2: 25%
- Day 3: 50%
- Day 4+: max_daily (default 50)

### Run Tracker (`services/run_tracker.py`)
`SkillRunTracker` publishes real-time SSE events via Redis pub/sub:
- Channel pattern: `skill-run:{offer_slug}:{campaign_slug}:{skill_id}`
- Methods: `log()`, `start_step()`, `complete_step()`, `fail_step()`, `finish()`
- Context manager support (`with SkillRunTracker(...) as tracker:`)

### Guardrails (`core/guardrails/validators.py`)
3-tier anti-hallucination system:
- **Tier 2 (automated):** Check copy length limits, unfilled placeholders, hallucination markers ("as an ai", "based on my training")
- **Tier 3 (human approval):** Flag aggressive CTAs ("act now", "limited time"), competitor comparisons

---

## API Clients

| Client | File | Purpose |
|--------|------|---------|
| Apollo.io | `clients/apollo/` (8 files) | Company search, contact enrichment, org enrichment, sequences (create/activate/enroll/pause), analytics |
| OpenAI | `clients/openai_client.py` | Copy generation (Skill 3), company classification (Skill 5), personalization, agent reasoning |
| Supabase | `clients/supabase_client.py` | Two singletons: service-role (full access) + anon-key (read-only) |

**Apollo.io is the single platform** — company search + contact enrichment + sequences + analytics.

All clients use `@lru_cache(maxsize=1)` for singleton instances.

---

## Agent System

### Architecture
4 domain-specific agents + 1 orchestrator, running as a staged Celery pipeline:

| Agent | Domain | File | Purpose |
|-------|--------|------|---------|
| Lead Quality | `lead` | `core/agents/lead_quality.py` | Detects false positives + missed opportunities |
| ICP Tuner | `icp` | `core/agents/icp_tuner.py` | Suggests scoring threshold/weight adjustments |
| Copy Optimizer | `copy` | `core/agents/copy_optimizer.py` | Analyzes variant performance, suggests copy changes |
| Orchestrator | `workflow` | `core/agents/orchestrator.py` | Reviews all results, plans skill dispatch order |

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
- Precedence order: lead-quality (3) > icp-tuner (2) > copy-optimizer (1) > orchestrator (0)
- Outcomes: `apply`, `suppress`, `defer`

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

### LLM Reasoning
All agent OpenAI calls route through `core/agents/llm_reasoning.py`:
- Model: `gpt-4o`
- Temperature: 0.3 (conservative)
- Response format: `json_object`
- Structured output: `{recommendations: [...], reasoning: "..."}`

---

## Vertical System

3 verticals supported: **staffing**, **ai-data-consulting**, **cloud-software-delivery**

- Playbooks: 8 `.md` files each under `context/verticals/{slug}/` (overview, icp, buyers, signals, scoring, messaging, objections, proof-points)
- Resolution: `campaign.vertical_id ?? offer.default_vertical_id`
- Entry point: `services/verticals/context_builder.py` — appends vertical context to skill prompts
- **ICP Builder (v2)** — `icp_profile JSONB` column is ABSOLUTE source of truth when not null
- Legacy scoring via `scoring_config_overrides` is completely ignored when `icp_profile` is set

---

## Gotchas & Non-Obvious Patterns

### Celery + Async
- Skills are **pure async functions** — Celery wraps them via `asgiref.async_to_sync`
- Never call `asyncio.run()` inside a Celery task — use `async_to_sync(fn)(args)` instead
- Task time limit is 600s — long-running skills (especially Skill 4) can hit this
- `bind=True` on tasks gives access to `self.request.id` for task correlation

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

### Logging (structlog)
- All modules use `structlog.get_logger()` — NOT stdlib `logging`
- Structured key-value logging: `logger.info("message", key=value, key2=value2)`
- JSON renderer in production, ConsoleRenderer when `LOG_LEVEL=debug`
- `configure_logging()` called once at app startup in lifespan

### Error Handling
- **Always use `to_app_error(err)`** before raising unknown errors in routes
- `AppError(message, status_code, code)` — machine-readable `code` field for frontend
- Routes: `try: ... except AppError: raise except Exception as exc: raise to_app_error(exc)`
- Never swallow exceptions silently — at minimum `logger.warning`

### SSE Streaming
- Skill runs publish events to Redis pub/sub channels
- Channel format: `skill-run:{offer_slug}:{campaign_slug or 'none'}:{skill_id}`
- SSE timeout: 600 seconds (10 minutes)
- Termination: `{"type": "done"}` event closes the stream
- Uses `redis.asyncio` for the subscriber and sync `redis` for the publisher (Celery tasks)

### Agent Security
- All `/api/agents/*` routes require `X-Agent-Secret` header
- Header validated against `agent_internal_secret` from config
- If `agent_internal_secret` is empty, returns 500 (not 403)

### Cost Optimization (Skill 4)
- Companies are **ICP-scored BEFORE contact enrichment** — below-threshold companies never enriched (saves Apollo credits)
- Geography rejection also runs before enrichment for the same reason
- Two-stage pipeline: Stage 1 (broad) -> enrich qualifying companies -> Stage 2 (strict scoring)

### Path Traversal Protection
- All artifact/status routes resolve paths and check `path.is_relative_to(offers_root)` before reading
- Never construct file paths from user input without this check

---

## Environment Variables

```bash
# Required — Core services
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
APOLLO_API_KEY=
OPENAI_API_KEY=

# Optional — Read-only access (matches frontend)
SUPABASE_ANON_KEY=

# Redis (Celery broker + SSE pub/sub)
REDIS_URL=redis://localhost:6379/0          # Default

# Agent system
AGENT_INTERNAL_SECRET=                      # Required for /api/agents/* routes

# Feature flags
ICP_BUILDER_ENABLED=true                    # Default: true (activate ICP v2 pipeline in Skill 4)

# Logging
LOG_LEVEL=info                              # debug | info | warning | error (default: info)

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Directories
CONTEXT_DIR=context                         # Path to expert knowledge .md files
OFFERS_DIR=offers                           # Path to per-offer output directory
```

All settings loaded via `pydantic-settings` from `.env` file (`app/config.py`).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API server won't start | Check `.env` exists with `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `APOLLO_API_KEY`, `OPENAI_API_KEY` |
| Skill runs stay "queued" | Redis not running — start with `docker run -d --name redis -p 6379:6379 redis:7-alpine` |
| Celery worker won't connect | Check `REDIS_URL` in .env; verify Redis is reachable |
| SSE stream never receives events | Celery worker not running — skill tasks execute in the worker, not the API server |
| Agent routes return 403 | Check `X-Agent-Secret` header matches `AGENT_INTERNAL_SECRET` in .env |
| Agent routes return 500 | `AGENT_INTERNAL_SECRET` is empty — set it in .env |
| Skill 3 copy fails | Check `OPENAI_API_KEY` has credits |
| Skill 4 returns 0 results | Geography filter excluding all companies — check `[GEOGRAPHY REJECT]` logs |
| Skill 4 timeout | Task time limit is 600s — reduce search scope or increase `task_time_limit` |
| Database errors | Ensure all 11 migrations (001-011) are applied in Supabase |
| Import errors | Run `uv sync` to install dependencies |
| Type errors | Run `uv run mypy .` — strict mode is enabled |
| Lint failures | Run `uv run ruff check . --fix` for auto-fixable issues |
| ICP Builder not activating | Set `ICP_BUILDER_ENABLED=true` in .env; ensure campaign has `icp_profile` saved |
| Tests fail with connection errors | Tests should mock external services — check `conftest.py` fixtures |

---

## Safety

### Email
- Apollo verifies emails automatically — use `email_status: 'verified'` filter
- Monitor bounce rate (<5%); health monitor auto-pauses sequences above threshold
- Enrollment ramp: 10% -> 25% -> 50% -> max over 4 days
- Never blast same generic message — signals must be referenced

### LinkedIn
- Manual only — never automate LinkedIn DMs (account ban risk)
- Max 5-10 LinkedIn actions per day via CEO account

### Deduplication
- `contacts(email)` UNIQUE constraint prevents duplicate enrichment
- `campaign_sequences(campaign_id, segment_key)` UNIQUE prevents duplicate sequences
- `campaign_companies` tracks which companies are in each campaign
- In-memory dedup runs before DB writes: `deduplicate_contacts()`, `deduplicate_companies()`

### Guardrails
- Tier 2 (automated): Copy length, placeholder validation, hallucination detection
- Tier 3 (human approval): Aggressive CTAs, competitor comparisons flagged for review
- Variants pending approval visible at `GET /api/variants/pending`
