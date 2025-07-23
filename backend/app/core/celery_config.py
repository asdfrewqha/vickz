import logging

from celery import Celery

from app.core.settings import settings


logging.info(settings.redis_settings.celery_url)

celery_app = Celery(main="app", broker=settings.redis_settings.celery_url, backend=settings.redis_settings.celery_back_url)

celery_app.autodiscover_tasks(packages=["app.api.auth"])
