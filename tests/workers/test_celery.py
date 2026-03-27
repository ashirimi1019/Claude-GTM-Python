"""Tests for Celery app factory, skill tasks, agent tasks, and scheduled tasks."""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestCeleryAppFactory:
    """Tests for create_celery_app()."""

    def test_create_celery_app_returns_celery_instance(self):
        from workers.celery_app import create_celery_app

        app = create_celery_app()
        assert app.main == "cirruslabs"

    def test_celery_app_config(self):
        from workers.celery_app import create_celery_app

        app = create_celery_app()
        assert app.conf.task_serializer == "json"
        assert app.conf.result_serializer == "json"
        assert app.conf.accept_content == ["json"]
        assert app.conf.timezone == "UTC"
        assert app.conf.task_track_started is True
        assert app.conf.task_time_limit == 600
        assert app.conf.task_soft_time_limit == 540

    def test_celery_app_beat_schedule(self):
        from workers.celery_app import create_celery_app

        app = create_celery_app()
        schedule = app.conf.beat_schedule
        assert "agent-daily-run" in schedule
        assert schedule["agent-daily-run"]["task"] == "run_agent_cron"
        assert "health-monitor" in schedule
        assert schedule["health-monitor"]["task"] == "run_health_monitor"
        assert "cleanup-stale-runs" in schedule
        assert schedule["cleanup-stale-runs"]["task"] == "cleanup_stale_runs"

    def test_celery_app_uses_redis_url_from_settings(self):
        from workers.celery_app import create_celery_app

        app = create_celery_app()
        # The broker URL should match REDIS_URL from test env
        broker_url = app.conf.broker_url
        assert "redis://" in broker_url

    def test_celery_app_singleton(self):
        from workers.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == "cirruslabs"


class TestSkillTasks:
    """Tests for skill task execution."""

    def test_run_skill_task_registered(self):
        from workers.celery_app import celery_app

        # Import to trigger registration
        import workers.skill_tasks  # noqa: F401

        assert "run_skill" in celery_app.tasks

    def test_run_skill_task_returns_result(self):
        from workers.skill_tasks import run_skill_task

        # Call the underlying function directly (not via Celery)
        # bind=True tasks need self, so we call .run() which skips the bind
        result = run_skill_task.apply(
            args=[1, "test-offer"],
            kwargs={"campaign_slug": "test-campaign"},
        ).result
        assert result["status"] == "completed"
        assert result["skill_id"] == 1
        assert result["offer_slug"] == "test-offer"
        assert result["campaign_slug"] == "test-campaign"

    def test_run_skill_task_without_campaign(self):
        from workers.skill_tasks import run_skill_task

        result = run_skill_task.apply(args=[3, "another-offer"]).result
        assert result["status"] == "completed"
        assert result["skill_id"] == 3
        assert result["campaign_slug"] is None


class TestAgentTasks:
    """Tests for agent pipeline tasks."""

    def test_agent_pipeline_registered(self):
        from workers.celery_app import celery_app

        import workers.agent_tasks  # noqa: F401

        assert "run_agent_pipeline" in celery_app.tasks
        assert "run_agent_step" in celery_app.tasks

    def test_run_agent_pipeline(self):
        from workers.agent_tasks import run_agent_pipeline

        result = run_agent_pipeline.apply(args=["agent-1"]).result
        assert result["status"] == "completed"
        assert result["agent_id"] == "agent-1"

    def test_run_agent_step(self):
        from workers.agent_tasks import run_agent_step

        result = run_agent_step.apply(
            args=["agent-1", "enrich"],
            kwargs={"payload": {"key": "value"}},
        ).result
        assert result["status"] == "completed"
        assert result["step_name"] == "enrich"


class TestScheduledTasks:
    """Tests for Celery Beat scheduled tasks."""

    def test_scheduled_tasks_registered(self):
        from workers.celery_app import celery_app

        import workers.scheduled_tasks  # noqa: F401

        assert "run_agent_cron" in celery_app.tasks
        assert "run_health_monitor" in celery_app.tasks
        assert "cleanup_stale_runs" in celery_app.tasks

    def test_run_agent_cron(self):
        from workers.scheduled_tasks import run_agent_cron

        result = run_agent_cron.apply().result
        assert result["status"] == "completed"
        assert result["task"] == "agent_cron"

    def test_run_health_monitor(self):
        from workers.scheduled_tasks import run_health_monitor

        result = run_health_monitor.apply().result
        assert result["status"] == "healthy"
        assert result["task"] == "health_monitor"

    def test_cleanup_stale_runs(self):
        from workers.scheduled_tasks import cleanup_stale_runs

        result = cleanup_stale_runs.apply().result
        assert result["status"] == "completed"
        assert result["task"] == "cleanup_stale_runs"
