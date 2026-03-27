# CirrusLabs Python Backend

**Stack:** Python 3.13 · FastAPI · Celery + Redis · Supabase · Apollo.io · OpenAI
**Repo:** https://github.com/ashirimi1019/Claude-GTM-Python

---

## Quick Start

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
uv run pytest -v
uv run pytest --tb=short -q  # Quick summary
```

---

## Architecture

```
app/           → FastAPI application (routes, config, errors, SSE)
core/skills/   → Skill 1-6 implementations (pure async functions)
core/agents/   → AI agent system (4 agents + orchestrator)
clients/       → Apollo (8 files), OpenAI, Supabase
services/      → Geography, scoring, dedup, personalization, intelligence, CSV
services/icp/  → ICP pipeline (normalizer, executor, validator, resolver, preview)
services/verticals/ → Vertical system (loader, resolver, context builder)
models/        → Pydantic v2 domain models
workers/       → Celery tasks (skills, agents, scheduled)
context/       → Expert knowledge (.md files — edit to tune the system)
offers/        → Per-offer + per-campaign outputs
tests/         → pytest test suite
```

---

## Commands

```bash
uv run pytest                           # Run all tests
uv run pytest tests/services/icp/ -v    # Run ICP tests only
uv run ruff check .                     # Lint
uv run mypy .                           # Type check
```

---

## Key Patterns

- **ICP Profile precedence:** `campaign.icp_profile > offer.icp_profile > legacy scoring_config_overrides`
- **Two-stage pipeline:** Stage 1 (broad) → enrich → Stage 2 (user strictness)
- **Geography before enrichment:** Saves Apollo credits
- **Pydantic models:** snake_case fields with camelCase aliases for DB JSONB compat
- **Skills are pure async functions:** Celery wraps them via `async_to_sync`
- **Frontend reads Supabase directly:** Only /api/ routes go through this backend
