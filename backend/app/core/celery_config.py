from celery import Celery

from app.core.settings import settings

from app.core.logging import get_logger

logger = get_logger()

logger.info(settings.redis_settings.celery_url)

celery_app = Celery(main="app", broker=settings.redis_settings.celery_url, backend=settings.redis_settings.celery_back_url)

celery_app.autodiscover_tasks(packages=["app.api.auth"])
