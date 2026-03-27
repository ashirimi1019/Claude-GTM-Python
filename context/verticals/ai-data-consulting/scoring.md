# AI & Data Consulting — Scoring Guide

> Scoring philosophy and weighted model for evaluating AI/data consulting leads. Aligns with the existing 170-point ICP threshold in scoring.ts.

---

## Scoring Philosophy

**Problem clarity > Company size.**

The best AI/data consulting leads are companies with a clearly articulated data or AI problem and urgency to solve it — regardless of whether they are a 200-person Series B or a 5,000-person enterprise. A mid-market company actively failing at ML production is a better lead than a Fortune 500 with a vague interest in AI.

Priority signals: active AI/ML hiring, data platform modernization projects, recent data leadership hires, public statements about AI strategy.

---

## Weighted Scoring Model (300 Points Total)

### Dimension 1: Data/AI Investment Signals (0-100 points)

| Signal | Points | Notes |
|--------|--------|-------|
| Hiring data engineers, ML engineers, or data scientists | 25-40 | More roles = higher signal strength |
| Recently hired CDO, Head of Data, or VP Analytics | 20-30 | New data leadership = budget and mandate |
| Job posts mention specific modern tools (Databricks, Snowflake, dbt, Airflow, MLflow) | 15-25 | Indicates active modernization |
| Public AI/data strategy announcements (press, blog, conference talks) | 10-20 | Shows executive commitment |
| Hiring for GenAI/LLM-specific roles | 15-25 | Emerging capability — high urgency signal |
| Active data platform migration (mentioned in job posts or tech blog) | 20-30 | Direct project signal |
| No observable data/AI investment signals | 0 | Do not pursue without confirming need |

### Dimension 2: Company Profile Fit (0-100 points)

| Factor | Points | Notes |
|--------|--------|-------|
| Revenue $20M-$500M (mid-market sweet spot) | 20-30 | Large enough for budget, small enough to need help |
| Series B-D funded (venture-backed growth stage) | 15-25 | Growth capital available, pressure to scale |
| Enterprise $500M+ with innovation/transformation mandate | 15-25 | Budget exists, but sales cycle longer |
| Tech-forward industry (fintech, healthtech, e-commerce, SaaS) | 10-20 | Higher data maturity baseline |
| Data-intensive business model (marketplace, financial services, logistics) | 15-25 | Natural need for advanced data capabilities |
| Engineering team 50-500 (enough to need help, not enough to do it all) | 10-20 | Capacity gap is real |
| Headcount <20 engineering or pre-Series A | 0-5 | Likely too early for consulting engagement |

### Dimension 3: Engagement Likelihood (0-100 points)

| Factor | Points | Notes |
|--------|--------|-------|
| Previous consulting engagement history (visible on LinkedIn, case studies) | 15-25 | Proven buyer of consulting services |
| Job posts indicate urgency (ASAP, immediate, critical hire) | 10-20 | Timeline pressure increases conversion |
| Multiple data/AI roles open simultaneously | 15-25 | Signals a program, not a single hire |
| Failed internal AI/data initiative (visible from role churn, re-orgs) | 15-25 | Pain is fresh and proven |
| Active RFP or vendor evaluation (if observable) | 20-30 | Direct buying signal |
| CTO/CDO publicly discussing data challenges (conference, podcast, blog) | 10-15 | Open to external perspectives |
| No engagement likelihood signals | 0 | Cold outreach with low conversion probability |

---

## Scoring Tiers

| Tier | Score Range | Action |
|------|------------|--------|
| Hot Lead | 220-300 | Priority outreach — strong signal + fit + engagement likelihood |
| Strong Match | 170-219 | Standard outreach — meets ICP threshold, good vertical fit |
| Warm | 120-169 | Nurture — monitor for signal strengthening before outreach |
| Low Priority | <120 | Do not enrich contacts — insufficient signal for AI/data consulting |

**Note:** The 170-point threshold aligns with the existing `scoring.ts` ICP threshold. Leads scoring 170+ should be enriched for contact discovery.

---

## Segment Scoring Guidance

Different AI/data consulting segments have distinct signal patterns:

| Segment | Primary Signals | Typical Score Boost |
|---------|----------------|-------------------|
| Data Platform Modernization | Legacy warehouse complaints, Snowflake/Databricks hiring, data engineer volume | +15-25 when multiple platform signals present |
| ML/AI Implementation | ML engineer hiring, MLOps tool mentions, failed internal ML attempts | +15-25 when production ML is explicitly sought |
| Analytics & BI | BI tool migration signals, analytics engineer hiring, self-service mentions | +10-20 for analytics modernization signals |
| GenAI/LLM Applications | LLM/GenAI role hiring, RAG mentions, responsible AI discussions | +15-25 for GenAI-specific signals (high urgency) |
| Data Governance & Quality | Data governance hiring, compliance mentions, data quality tool adoption | +10-15 typically paired with other segments |

---

## Disqualification Criteria

Automatically disqualify (score = 0) if any apply:

- Company has a mature internal data platform team (50+ data engineers) — they build, not buy
- Pure research/academic institution with no commercial product
- Government entity requiring security clearances we cannot provide
- Company publicly committed to a competing consulting firm for data work
- No observable data or technology footprint (non-tech company with no digital ambition)

---

## Alignment with Existing Scoring

These weights are **starter guidance** for the AI & Data Consulting vertical. They are designed to:

1. Work alongside the existing `scoring.ts` ICP scoring (which uses a 170-point threshold)
2. Provide vertical-specific signal interpretation (e.g., data engineer hiring is weighted higher here than in staffing)
3. Be refined based on campaign results — Skill 6 learnings should update these weights over time
4. Eventually feed into programmatic scoring when `scoring.ts` becomes vertical-configurable

The qualitative guidance here should influence how Skill 4 interprets search results and how Skill 5 prioritizes segments for outreach.


## Scoring Config
```yaml
# Threshold raised 170 → 180 (2026-03-18).
# Rationale: keyword list is already specific to AI/data stack so keyword floor fires meaningfully.
# Raising to 180 eliminates the "signal + optimal size + preferred funding = 180" exact-boundary pass —
# companies at that floor now need domain(10) or keyword match to confirm tech depth.
threshold: 180
dimensions:
  hiring_signal: 100
  company_size_optimal: 50
  company_size_acceptable: 30
  funding: 30
  revenue: 20
  tech_keywords: 20
  domain: 10
# Size bands — AI/data consulting targets larger companies with bigger data budgets.
# 200-5000 is the sweet spot (enough data volume to need external consulting).
optimal_size_min: 200
optimal_size_max: 5000
acceptable_size_max: 10000
partial_size_min: 50
# Revenue floor — $20M+ indicates budget for consulting engagements.
min_revenue: 20000000
tech_keywords:
  - machine learning
  - ai
  - data platform
  - data engineering
  - mlops
  - databricks
  - snowflake
  - spark
  - dbt
  - airflow
  - llm
  - generative ai
  - data lake
  - data warehouse
  - vector database
  - openai
  - hugging face
  - pytorch
  - tensorflow
  - python
  - kafka
  - flink
disqualify_sectors:
  - government
  - academia
  - pure research
  # Added 2026-03-18 — non-buyers or structural competitors:
  - outsourcing
  - bpo
  - management consulting
  - pure media
  - content marketing
# Preferred stages receive full funding-dimension credit (30 pts).
# Funded stages not on this list receive partial credit (15 pts).
# Series B–D = ideal: growth capital deployed, data/AI mandate established, budget available.
# Series A = acceptable: earlier in data maturity journey, smaller engagement scope.
# IPO/Public/Enterprise = partial: longer sales cycle, heavy procurement process.
preferred_funding_stages:
  - series_b
  - series_c
  - series_d
# Hard-exclude stages (no enrichment, no outreach).
# Pre-Seed/Seed = too early for consulting engagement economics; data platform is still being built,
#   budget for external consulting rarely approved at this stage.
excluded_funding_stages:
  - seed
  - pre_seed
  - pre-seed
```