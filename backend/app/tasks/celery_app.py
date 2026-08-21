from __future__ import annotations

import os

from celery import Celery

broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

celery_app = Celery(
    "cryptotracker",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.sync_coins"],  # Explicitly include task modules
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=120,
    task_time_limit=180,
    broker_connection_retry_on_startup=True,
)

# Beat schedule: sync coin metadata every 60 seconds
celery_app.conf.beat_schedule = {
    "sync-coin-metadata-every-60s": {
        "task": "app.tasks.sync_coins.sync_coin_metadata",
        "schedule": 60.0,
    },
}
