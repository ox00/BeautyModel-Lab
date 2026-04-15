from celery import Celery
from celery.schedules import crontab

from app.config.settings import settings

celery_app = Celery(
    "trend_crawler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.tasks.crawl_tasks.*": {"queue": "crawl"},
        "app.tasks.clean_tasks.*": {"queue": "process"},
        "app.tasks.schedule_tasks.*": {"queue": "schedule"},
    },

    # Task execution
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    task_soft_time_limit=1500,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,

    # Result expiration
    result_expires=3600,

    # Beat schedule - daily crawl tasks per platform
    beat_schedule={
        "crawl-xhs-daily": {
            "task": "app.tasks.schedule_tasks.scheduled_crawl",
            "schedule": crontab(hour=8, minute=0),
            "args": ("xhs",),
        },
        "crawl-douyin-daily": {
            "task": "app.tasks.schedule_tasks.scheduled_crawl",
            "schedule": crontab(hour=8, minute=30),
            "args": ("dy",),
        },
        "crawl-bilibili-daily": {
            "task": "app.tasks.schedule_tasks.scheduled_crawl",
            "schedule": crontab(hour=9, minute=0),
            "args": ("bili",),
        },
        "crawl-weibo-daily": {
            "task": "app.tasks.schedule_tasks.scheduled_crawl",
            "schedule": crontab(hour=9, minute=30),
            "args": ("wb",),
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
