"""Celery app factory and singleton instance."""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    settings = get_settings()
    app = Celery("cirruslabs", broker=settings.redis_url, backend=settings.redis_url)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        task_track_started=True,
        task_time_limit=600,
        task_soft_time_limit=540,
    )
    app.conf.beat_schedule = {
        "agent-daily-run": {
            "task": "run_agent_cron",
            "schedule": crontab(hour=9, minute=0),
        },
        "health-monitor": {
            "task": "run_health_monitor",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "cleanup-stale-runs": {
            "task": "cleanup_stale_runs",
            "schedule": crontab(hour=3, minute=0),
        },
    }
    return app


celery_app = create_celery_app()
