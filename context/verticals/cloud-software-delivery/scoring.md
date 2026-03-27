# Cloud & Software Delivery — Scoring Guide

> Scoring philosophy and weighted model for evaluating cloud/software delivery leads. Aligns with the existing 170-point ICP threshold in scoring.ts.

---

## Scoring Philosophy

**Project urgency > Perpetual need.**

The best cloud/software delivery leads are companies with a specific, time-bound project or initiative driving their need — not companies that perpetually need engineers. A company migrating to the cloud by Q4 deadline is a better lead than one that always has open engineering reqs. Look for transformation signals, not steady-state hiring.

Priority signals: cloud migration announcements, platform engineering hiring, DevOps/SRE leadership hires, infrastructure modernization mentions in job posts, compliance deadlines driving cloud adoption.

---

## Weighted Scoring Model (300 Points Total)

### Dimension 1: Cloud/Engineering Investment Signals (0-100 points)

| Signal | Points | Notes |
|--------|--------|-------|
| Hiring cloud architects, platform engineers, or SREs | 25-40 | Core signal — building or modernizing infrastructure |
| Recently hired VP Engineering, CTO, or Head of Platform | 20-30 | New technical leadership = new initiatives |
| Job posts mention cloud migration, modernization, or re-architecture | 20-30 | Direct project signal |
| Kubernetes, Terraform, or IaC tool mentions in job posts | 15-25 | Platform modernization in progress |
| DevOps/SRE practice buildout signals (SLO, observability mentions) | 15-20 | Maturity advancement — ready for expert help |
| Cloud cost optimization or FinOps hiring | 10-15 | Post-migration optimization phase |
| No observable cloud/engineering investment signals | 0 | Do not pursue without confirming need |

### Dimension 2: Company Profile Fit (0-100 points)

| Factor | Points | Notes |
|--------|--------|-------|
| Engineering team 50-500 (enough complexity, capacity gap is real) | 20-30 | Sweet spot for delivery augmentation |
| Revenue $20M-$1B (budget for external engineering) | 15-25 | Can afford consulting-rate engineers |
| Series B-D funded with growth pressure | 15-25 | Need to ship fast, cannot wait for hiring |
| Enterprise with digital transformation mandate | 15-25 | Budget allocated, timeline pressure |
| Tech-forward industry (SaaS, fintech, e-commerce, healthtech) | 10-20 | Cloud-native trajectory |
| Multi-product company or platform business | 10-15 | Platform engineering is a force multiplier |
| Pre-Series A or <20 engineers | 0-5 | Too small for consulting engagement economics |

### Dimension 3: Engagement Likelihood (0-100 points)

| Factor | Points | Notes |
|--------|--------|-------|
| Deadline-driven project (compliance, product launch, migration date) | 20-30 | Time pressure is the strongest conversion signal |
| Previous use of engineering consultants or contractors | 15-25 | Proven buyer of external engineering |
| Job posts open for 60+ days (struggling to hire) | 15-25 | Hiring difficulty increases consulting appeal |
| Multiple infrastructure roles open simultaneously | 15-20 | Signals a program, not a single hire |
| CTO/VP Eng publicly discussing technical debt or scaling challenges | 10-15 | Open to external help |
| Active vendor evaluation for cloud or DevOps tooling | 10-20 | In buying mode for infrastructure services |
| No engagement likelihood signals | 0 | Cold outreach with low conversion probability |

---

## Scoring Tiers

| Tier | Score Range | Action |
|------|------------|--------|
| Hot Lead | 220-300 | Priority outreach — strong project signal + fit + urgency |
| Strong Match | 170-219 | Standard outreach — meets ICP threshold, good vertical fit |
| Warm | 120-169 | Nurture — monitor for project signals before outreach |
| Low Priority | <120 | Do not enrich contacts — insufficient signal for cloud/delivery |

**Note:** The 170-point threshold aligns with the existing `scoring.ts` ICP threshold. Leads scoring 170+ should be enriched for contact discovery.

---

## Segment Scoring Guidance

Different cloud/software delivery segments have distinct signal patterns:

| Segment | Primary Signals | Typical Score Boost |
|---------|----------------|-------------------|
| Cloud Migration | Cloud architect hiring, migration mentions, legacy infrastructure complaints | +20-30 when migration timeline is observable |
| Platform Engineering | Platform engineer hiring, Kubernetes/IaC mentions, developer platform references | +15-25 when platform buildout is explicitly signaled |
| Software Delivery Acceleration | CI/CD mentions, release engineering hiring, deployment frequency complaints | +10-20 for delivery pipeline modernization |
| DevOps/SRE Transformation | SRE hiring, observability mentions, incident management tool adoption | +15-20 when SRE practice is being established |
| Team Augmentation | Multiple senior engineering roles open 60+ days, deadline-driven hiring | +15-25 when hiring urgency is clear |

---

## Disqualification Criteria

Automatically disqualify (score = 0) if any apply:

- Company has a mature platform engineering team (20+ platform engineers) — they build internally
- Pure agency/consultancy (we do not sub-contract to other consultancies)
- Government entity requiring clearances we cannot provide
- Company publicly committed to a competing consulting/delivery firm
- On-premise only with no cloud adoption intent (rare but exists in regulated industries)
- Company in active downsizing or layoffs (no budget for external engineering)

---

## Alignment with Existing Scoring

These weights are **starter guidance** for the Cloud & Software Delivery vertical. They are designed to:

1. Work alongside the existing `scoring.ts` ICP scoring (which uses a 170-point threshold)
2. Provide vertical-specific signal interpretation (e.g., cloud architect hiring is weighted higher here than in staffing or AI/data)
3. Be refined based on campaign results — Skill 6 learnings should update these weights over time
4. Eventually feed into programmatic scoring when `scoring.ts` becomes vertical-configurable

The qualitative guidance here should influence how Skill 4 interprets search results and how Skill 5 prioritizes segments for outreach.


## Scoring Config
```yaml
# Threshold raised 170 → 180 (2026-03-18).
# Rationale: keyword list is already cloud/infra-specific (kubernetes, terraform, argocd, etc.).
# Raising to 180 removes the free pass for companies that score signal + size + funding without any
# observable cloud tooling — they must now also have domain(10) or a keyword match to qualify.
threshold: 180
dimensions:
  hiring_signal: 100
  company_size_optimal: 50
  company_size_acceptable: 30
  funding: 30
  revenue: 20
  tech_keywords: 20
  domain: 10
# Size bands — cloud delivery engagements scale with company size. Wider range than staffing.
# 100-5000 = sweet spot (enough infra complexity to need external delivery).
optimal_size_min: 100
optimal_size_max: 5000
acceptable_size_max: 10000
partial_size_min: 50
# Revenue floor — $20M+ indicates budget for delivery engagements.
min_revenue: 20000000
tech_keywords:
  - kubernetes
  - docker
  - terraform
  - aws
  - gcp
  - azure
  - cloud native
  - devops
  - platform engineering
  - sre
  - microservices
  - ci/cd
  - infrastructure as code
  - helm
  - istio
  - observability
  - argocd
  - gitops
  - finops
  - prometheus
  - grafana
disqualify_sectors:
  - government
  - academia
  - on-premise only
  # Added 2026-03-18 — MSPs/VARs/BPOs are competitors or resellers, not buyers:
  - managed services provider
  - msp
  - outsourcing
  - bpo
  - value added reseller
  - var
  - management consulting
# Preferred stages receive full funding-dimension credit (30 pts).
# Funded stages not on this list receive partial credit (15 pts).
# Series B–D = ideal: growth pressure + shipping deadline + budget for external delivery.
# Series A = acceptable: earlier-stage, smaller delivery scope, budget tighter.
# IPO/Public/Enterprise = partial: budget exists but procurement is process-heavy.
preferred_funding_stages:
  - series_b
  - series_c
  - series_d
# Hard-exclude stages (no enrichment, no outreach).
# Added seed/pre_seed 2026-03-18: icp.md flags "Pre-revenue startups" and "<50 employees" as
# too small for delivery engagement economics. Seed/pre-seed companies should not be enriched.
excluded_funding_stages:
  - seed
  - pre_seed
  - pre-seed
```
