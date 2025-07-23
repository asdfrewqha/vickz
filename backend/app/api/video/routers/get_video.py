from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.core.logging import get_logger
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import Video, User, Like
from app.database.session import get_async_session
from app.api.video.schemas import VideoResponse

router = APIRouter()
Bear = HTTPBearer(auto_error=False)

logger = get_logger()


@router.get("/get-video", response_model=VideoResponse)
async def get_video(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    stmt = select(Video).order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    random_video = result.scalar_one_or_none()

    if not random_video:
        raise HTTPException(status_code=404, detail="No videos found")

    author = await session.get(User, random_video.author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    like_objs = await adapter.get_by_values(
        Like,
        {"user_id": user.id, "video_id": random_video.id},
        session=session,
    )
    like_obj = like_objs[0] if like_objs else None

    liked = like_obj.like is True if like_obj else False
    disliked = like_obj.like is False if like_obj else False

    response = VideoResponse.model_validate(random_video, from_attributes=True)
    response.serv_url = f"{settings.backend_url}/stream-video/{random_video.id}"
    response.author_name = author.name
    response.author_username = author.username
    response.is_liked_by_user = liked
    response.is_disliked_by_user = disliked

    return response
