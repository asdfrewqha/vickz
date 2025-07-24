import logging
import os
from typing import Annotated
from urllib.parse import urlparse
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.dependencies.checks import check_user_token
from app.dependencies.responses import emptyresponse
from app.dependencies.s3_buckets import get_s3_b2
from app.database.adapter import adapter
from app.database.session import get_async_session
from app.database.models import User, Video
from app.utils.s3_adapter import S3HttpxSigV4Adapter


router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_file_suffix(url: str) -> str:
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    return ext.lstrip(".")


s3 = S3HttpxSigV4Adapter(settings.s3_settings.bucket2)


@router.delete("/delete-video/{uuid}", status_code=204)
async def delete_video(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    s3: Annotated[S3HttpxSigV4Adapter, Depends(get_s3_b2)],
):
    video_result = await adapter.get_by_id(Video, uuid, session=session)
    if not video_result:
        raise HTTPException(404, "Video not found")
    if video_result.author_id != user.id:
        raise HTTPException(403, "Forbidden")

    filepath = f"{uuid}.{get_file_suffix(video_result.url)}"
    await s3.delete_file(filepath)
    logger.info(filepath)
    await adapter.delete(Video, uuid, session=session)
    return emptyresponse()
