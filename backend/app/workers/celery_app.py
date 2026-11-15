from celery import Celery
from app.config import settings

celery = Celery(
    "resume_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
        "app.workers.browser_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.browser_tasks.*": {"queue": "browser"},
        "app.workers.tasks.*": {"queue": "default"},
    },
    task_default_queue="default",
)