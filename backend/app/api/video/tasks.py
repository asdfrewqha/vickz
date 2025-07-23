import os
import tempfile

from app.api.video.utils import compress_video_sync, gen_blur_sync, is_horizontal_sync
from app.core.celery_config import celery_app


@celery_app.task
def process_video_task(input_path: str) -> str:
    horizontal = is_horizontal_sync(input_path)

    if horizontal:
        return gen_blur_sync(input_path)

    size = os.path.getsize(input_path)
    if size < 50 * 1024 * 1024:
        return input_path

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as out:
        compress_video_sync(input_path, out.name)
        return out.name
