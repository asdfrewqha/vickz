from typing import Annotated, List, Optional
from uuid import UUID

from app.api.video.schemas import VideoResponse
from app.core.settings import settings
from app.database.adapter import adapter
from app.database.models import User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/get-videos-by-user-id/{uuid}", response_model=List[Optional[VideoResponse]])
async def get_videos_by_user_id(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    author = await adapter.get_by_id(User, uuid)
    if not author:
        raise HTTPException(404, "User not found")
    videos = await adapter.get_by_value(Video, "author_id", uuid, session=session)
    if not videos:
        raise HTTPException(404, "Videos not found")
    response = []
    for video in videos:
        video = VideoResponse.model_validate(video)
        video.serv_url = f"{settings.backend_url}/stream-video/{video.id}"
        video.author_name = author.name
        video.author_username = author.username
        response.append(video)
    return response
