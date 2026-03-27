"""Celery tasks for the agent pipeline (stubs)."""

from __future__ import annotations

import logging

from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_agent_pipeline")
def run_agent_pipeline(self, agent_id: str, context: dict | None = None):
    """Run a full agent pipeline. Stub — real implementation later."""
    logger.info("Agent pipeline started: agent_id=%s task_id=%s", agent_id, self.request.id)
    return {"status": "completed", "agent_id": agent_id, "task_id": self.request.id}


@celery_app.task(bind=True, name="run_agent_step")
def run_agent_step(self, agent_id: str, step_name: str, payload: dict | None = None):
    """Run a single agent step. Stub — real implementation later."""
    logger.info(
        "Agent step started: agent_id=%s step=%s task_id=%s",
        agent_id,
        step_name,
        self.request.id,
    )
    return {
        "status": "completed",
        "agent_id": agent_id,
        "step_name": step_name,
        "task_id": self.request.id,
    }
