"""Celery tasks for the AI agent pipeline — wired to real agent implementations."""

from __future__ import annotations

import structlog
from asgiref.sync import async_to_sync

from workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(bind=True, name="run_agent_pipeline")
def run_agent_pipeline(
    self,
    offer_slug: str,
    campaign_slug: str,
):
    """Run the full staged agent pipeline for a campaign.

    Pipeline: Phase A (lead-quality) → Phase B (icp-tuner → copy-optimizer → orchestrator)
    Conflict resolution runs between phases.
    """
    logger.info(
        "Agent pipeline started",
        offer_slug=offer_slug,
        campaign_slug=campaign_slug,
        task_id=self.request.id,
    )

    try:
        from core.agents.snapshot import build_snapshot
        from core.agents.lead_quality import run_lead_quality
        from core.agents.icp_tuner import run_icp_tuner
        from core.agents.copy_optimizer import run_copy_optimizer
        from core.agents.orchestrator import run_orchestrator
        from core.agents.conflict_detector import detect_conflicts
        from core.agents.context_builder import build_prior_context
        from core.agents.action_executor import execute_actions

        # Build campaign snapshot
        snapshot = async_to_sync(build_snapshot)(campaign_slug)

        # Phase A: Lead Quality (runs first, highest domain precedence)
        lead_result = async_to_sync(run_lead_quality)(snapshot, prior=None)
        all_results = [lead_result]

        # Build context for Phase B agents
        prior = build_prior_context(all_results, snapshot.get("health", {}))

        # Phase B: ICP Tuner → Copy Optimizer → Orchestrator
        icp_result = async_to_sync(run_icp_tuner)(snapshot, prior=prior)
        all_results.append(icp_result)

        prior = build_prior_context(all_results, snapshot.get("health", {}))
        copy_result = async_to_sync(run_copy_optimizer)(snapshot, prior=prior)
        all_results.append(copy_result)

        orchestrator_result = async_to_sync(run_orchestrator)(snapshot, all_results)
        all_results.append(orchestrator_result)

        # Conflict resolution
        conflicts = detect_conflicts(all_results)

        # Collect safe recommendations for auto-apply
        safe_recs = []
        for result in all_results:
            for rec in result.recommendations:
                # Check if this recommendation was suppressed by conflict resolution
                suppressed = any(
                    c.outcome == "suppress" and c.domain == rec.domain
                    for c in conflicts
                )
                if not suppressed and rec.risk_level == "safe":
                    safe_recs.append(rec)

        # Auto-apply safe actions
        applied = async_to_sync(execute_actions)(safe_recs, snapshot.get("campaign_id", ""))

        return {
            "status": "completed",
            "task_id": self.request.id,
            "agents_run": len(all_results),
            "conflicts_resolved": len(conflicts),
            "actions_applied": len(applied),
        }

    except Exception as e:
        logger.error("Agent pipeline failed", error=str(e), exc_info=True)
        return {
            "status": "failed",
            "task_id": self.request.id,
            "error": str(e),
        }


@celery_app.task(bind=True, name="run_agent_cron")
def run_agent_cron(self):
    """Daily cron: run agent pipeline on all autonomous campaigns.

    Called by Celery Beat at 9am UTC daily.
    """
    logger.info("Agent cron started", task_id=self.request.id)

    # TODO: Query campaigns where autonomy_level = 'autonomous'
    # For each: dispatch run_agent_pipeline.delay(offer_slug, campaign_slug)

    return {"status": "completed", "campaigns_processed": 0}
