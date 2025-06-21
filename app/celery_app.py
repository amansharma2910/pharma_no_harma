from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "health_records",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]  # Include task modules
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure task routing
celery_app.conf.task_routes = {
    "app.tasks.file_tasks.*": {"queue": "file_processing"},
    "app.tasks.ai_tasks.*": {"queue": "ai_processing"},
    "app.tasks.export_tasks.*": {"queue": "export"},
} 