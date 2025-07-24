import os
import tempfile
from typing import Annotated, Optional

from app.api.video.schemas import VideoCreateResponse
from app.api.video.tasks import process_video_task
from app.core.logging import get_logger
from app.core.settings import settings
from app.database.adapter import adapter
from app.database.models import User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from app.dependencies.responses import badresponse
from app.dependencies.s3_buckets import get_s3_b2
from app.utils.s3_adapter import S3HttpxSigV4Adapter
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_v7.base import uuid7

router = APIRouter()
logger = get_logger()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".flv", ".wmv", ".m4v"}


@router.post("/upload-video", response_model=VideoCreateResponse, status_code=201)
async def upload_video(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    s3: Annotated[S3HttpxSigV4Adapter, Depends(get_s3_b2)],
    file: UploadFile = File(...),
    description: str = Form(""),
):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return badresponse("Unsupported file", 415)

    uuid = uuid7()
    s3_path = f"{uuid}{ext}"

    temp_input_path: Optional[str] = None
    output_path: Optional[str] = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_input_path = tmp.name
            while chunk := await file.read(1024 * 1024):
                tmp.write(chunk)

        result = process_video_task.delay(temp_input_path)
        output_path = await run_in_threadpool(result.get, timeout=900)
        if os.path.getsize(output_path) <= 5 * 1024 * 1024:
            public_url = await s3.upload_file(output_path, s3_path)
        else:
            public_url = await s3.upload_file_multipart(output_path, s3_path)

        await adapter.insert(
            Video,
            {
                "id": str(uuid),
                "author_id": user.id,
                "url": public_url,
                "description": description,
            },
            session=session,
        )

        return VideoCreateResponse(
            url=f"{settings.backend_url}/stream-video/{uuid}", uuid=str(uuid)
        )

    except Exception:
        logger.exception("Video upload failed")
        return badresponse("Internal server error", 500)

    finally:
        for path in [temp_input_path, output_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    logger.warning(f"Failed to remove temp file: {path}")
