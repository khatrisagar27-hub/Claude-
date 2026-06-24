"""Celery application configuration."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "cae",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "daily-audit-run": {
            "task": "app.workers.tasks.daily_audit_all_companies",
            "schedule": 86400,
        },
    },
)
