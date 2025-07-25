from app.core.logging import get_logger
from app.core.settings import settings
from celery import Celery

logger = get_logger()

logger.info(settings.redis_settings.celery_url)

celery_app = Celery(
    main="app",
    broker=settings.redis_settings.celery_url,
    backend=settings.redis_settings.celery_back_url,
)

celery_app.autodiscover_tasks(packages=["app.api.auth"])
celery_app.autodiscover_tasks(packages=["app.api.video"])
