"""Skill 6 — Campaign Review: fetch metrics, analyze, generate learnings.

Phases:
  a. Fetch Apollo sequence metrics for all campaign sequences
  b. Analyze: open rates, reply rates, bounce rates vs baseline
  c. Generate learnings.md
  d. Update global what-works.md
  e. Update vertical-specific learnings if applicable
  f. Return summary
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from clients.apollo.analytics import get_sequence_analytics

logger = structlog.get_logger()

# Industry baseline rates for comparison
BASELINE = {
    "open_rate": 0.25,
    "reply_rate": 0.03,
    "bounce_rate": 0.05,
    "click_rate": 0.02,
}


async def run_skill_6(
    offer_slug: str,
    campaign_slug: str,
    offers_dir: str = "offers",
    *,
    apollo_api_key: str = "",
    db_load_sequences: Any | None = None,
    context_dir: str = "context",
    vertical_slug: str | None = None,
) -> dict[str, Any]:
    """Execute Skill 6: Campaign Review.

    Returns {"sequences_analyzed": int, "learnings_written": bool}.
    """
    log = logger.bind(skill=6, offer=offer_slug, campaign=campaign_slug)
    log.info("Skill 6 started")

    campaign_dir = Path(offers_dir) / offer_slug / "campaigns" / campaign_slug

    # ── a. Fetch sequence metrics ──
    sequence_ids = await _get_sequence_ids(
        offer_slug, campaign_slug, db_load_sequences
    )
    log.info("Sequences to analyze", count=len(sequence_ids))

    all_metrics: list[dict[str, Any]] = []
    for seq_id in sequence_ids:
        try:
            metrics = await get_sequence_analytics(seq_id, api_key=apollo_api_key)
            all_metrics.append(metrics)
        except Exception as e:
            log.warn("Failed to fetch metrics", sequence_id=seq_id, error=str(e))

    # ── b. Analyze performance ──
    analysis = analyze_metrics(all_metrics)
    log.info("Analysis complete", **{k: v for k, v in analysis.items() if isinstance(v, (int, float, str))})

    # ── c. Generate learnings.md ──
    learnings_content = generate_learnings_md(
        offer_slug=offer_slug,
        campaign_slug=campaign_slug,
        metrics=all_metrics,
        analysis=analysis,
    )

    results_dir = campaign_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    learnings_path = results_dir / "learnings.md"
    learnings_path.write_text(learnings_content, encoding="utf-8")
    log.info("Learnings written", path=str(learnings_path))

    # ── d. Update global what-works.md ──
    what_works_path = Path(context_dir) / "learnings" / "what-works.md"
    _append_to_what_works(what_works_path, offer_slug, campaign_slug, analysis)

    # ── e. Update vertical-specific learnings ──
    if vertical_slug:
        vertical_learnings_path = (
            Path(context_dir) / "verticals" / vertical_slug / "learnings.md"
        )
        _append_to_what_works(
            vertical_learnings_path, offer_slug, campaign_slug, analysis
        )

    result = {
        "sequences_analyzed": len(all_metrics),
        "learnings_written": True,
    }
    log.info("Skill 6 complete", **result)
    return result


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyze_metrics(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze sequence metrics against baselines.

    Returns aggregated rates, per-sequence breakdown, and verdicts.
    """
    if not metrics:
        return {
            "total_sent": 0,
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "bounce_rate": 0.0,
            "click_rate": 0.0,
            "verdicts": [],
            "recommendations": ["No sequences to analyze — run Skill 5 first."],
        }

    total_sent = sum(m.get("sent", 0) for m in metrics)
    total_opened = sum(m.get("opened", 0) for m in metrics)
    total_replied = sum(m.get("replied", 0) for m in metrics)
    total_bounced = sum(m.get("bounced", 0) for m in metrics)
    total_clicked = sum(m.get("clicked", 0) for m in metrics)

    open_rate = total_opened / total_sent if total_sent > 0 else 0.0
    reply_rate = total_replied / total_sent if total_sent > 0 else 0.0
    bounce_rate = total_bounced / total_sent if total_sent > 0 else 0.0
    click_rate = total_clicked / total_sent if total_sent > 0 else 0.0

    verdicts = []
    recommendations = []

    # Open rate verdict
    if open_rate >= BASELINE["open_rate"] * 1.5:
        verdicts.append("open_rate: excellent")
    elif open_rate >= BASELINE["open_rate"]:
        verdicts.append("open_rate: above_baseline")
    else:
        verdicts.append("open_rate: below_baseline")
        recommendations.append("Improve subject lines — open rate is below industry baseline.")

    # Reply rate verdict
    if reply_rate >= BASELINE["reply_rate"] * 2:
        verdicts.append("reply_rate: excellent")
    elif reply_rate >= BASELINE["reply_rate"]:
        verdicts.append("reply_rate: above_baseline")
    else:
        verdicts.append("reply_rate: below_baseline")
        recommendations.append("Improve personalization and value proposition — reply rate is low.")

    # Bounce rate verdict
    if bounce_rate > BASELINE["bounce_rate"]:
        verdicts.append("bounce_rate: high")
        recommendations.append(
            "Bounce rate exceeds 5% threshold — verify email quality and consider pausing affected sequences."
        )
    else:
        verdicts.append("bounce_rate: acceptable")

    # Click rate verdict
    if click_rate >= BASELINE["click_rate"]:
        verdicts.append("click_rate: above_baseline")
    else:
        verdicts.append("click_rate: below_baseline")

    if not recommendations:
        recommendations.append("Campaign performing well — maintain current approach.")

    return {
        "total_sent": total_sent,
        "total_opened": total_opened,
        "total_replied": total_replied,
        "total_bounced": total_bounced,
        "total_clicked": total_clicked,
        "open_rate": round(open_rate, 4),
        "reply_rate": round(reply_rate, 4),
        "bounce_rate": round(bounce_rate, 4),
        "click_rate": round(click_rate, 4),
        "verdicts": verdicts,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Learnings generation
# ---------------------------------------------------------------------------


def generate_learnings_md(
    offer_slug: str,
    campaign_slug: str,
    metrics: list[dict[str, Any]],
    analysis: dict[str, Any],
) -> str:
    """Generate a learnings.md file from campaign metrics and analysis."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    total_sent = analysis.get("total_sent", 0)

    lines = [
        f"# Campaign Review: {offer_slug} / {campaign_slug}",
        f"_Generated: {now}_",
        "",
        "## Summary",
        f"- **Sequences analyzed:** {len(metrics)}",
        f"- **Total emails sent:** {total_sent}",
        f"- **Open rate:** {analysis.get('open_rate', 0):.1%}",
        f"- **Reply rate:** {analysis.get('reply_rate', 0):.1%}",
        f"- **Bounce rate:** {analysis.get('bounce_rate', 0):.1%}",
        f"- **Click rate:** {analysis.get('click_rate', 0):.1%}",
        "",
        "## Verdicts",
    ]

    for v in analysis.get("verdicts", []):
        lines.append(f"- {v}")

    lines.extend(["", "## Recommendations"])
    for r in analysis.get("recommendations", []):
        lines.append(f"- {r}")

    lines.extend(["", "## Per-Sequence Breakdown"])
    for m in metrics:
        sent = m.get("sent", 0)
        lines.append(f"### {m.get('name', m.get('sequence_id', 'unknown'))}")
        lines.append(f"- Sent: {sent}")
        lines.append(f"- Opened: {m.get('opened', 0)}")
        lines.append(f"- Replied: {m.get('replied', 0)}")
        lines.append(f"- Bounced: {m.get('bounced', 0)}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_sequence_ids(
    offer_slug: str,
    campaign_slug: str,
    db_loader: Any | None,
) -> list[str]:
    """Get sequence IDs from DB or return empty list."""
    if db_loader:
        sequences = await db_loader(offer_slug, campaign_slug)
        if sequences:
            return [s.get("apollo_sequence_id", "") for s in sequences if s.get("apollo_sequence_id")]
    return []


def _append_to_what_works(
    filepath: Path,
    offer_slug: str,
    campaign_slug: str,
    analysis: dict[str, Any],
) -> None:
    """Append a campaign learning entry to what-works.md."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).strftime("%Y-%m-%d")

    entry = (
        f"\n\n---\n"
        f"### {offer_slug} / {campaign_slug} ({now})\n"
        f"- Open rate: {analysis.get('open_rate', 0):.1%}\n"
        f"- Reply rate: {analysis.get('reply_rate', 0):.1%}\n"
        f"- Bounce rate: {analysis.get('bounce_rate', 0):.1%}\n"
    )

    for r in analysis.get("recommendations", []):
        entry += f"- Lesson: {r}\n"

    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        filepath.write_text(existing + entry, encoding="utf-8")
    else:
        header = "# What Works — Campaign Learnings\n\nAutomatically updated by Skill 6.\n"
        filepath.write_text(header + entry, encoding="utf-8")
