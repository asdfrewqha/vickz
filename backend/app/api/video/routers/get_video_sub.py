from random import choice
from typing import Annotated
from uuid import UUID

from app.api.video.schemas import VideoResponse
from app.core.logging import get_logger
from app.core.settings import settings
from app.database.adapter import adapter
from app.database.models import Like, Subscription, User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
Bear = HTTPBearer(auto_error=False)

logger = get_logger()


@router.get("/get-video/{uuid}", response_model=VideoResponse)
async def get_video(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    subscriptions = await adapter.get_by_value(
        Subscription, "subscriber_id", user.id, session=session
    )
    sub_list = [sub.subscribed_to_id for sub in subscriptions]
    video_list = []
    for sub in sub_list:
        video = await adapter.get_by_value(Video, "author_id", sub, session=session)
        if video:
            video_list.append(video)
    if not video_list:
        raise HTTPException(404, "Videos not found")
    rand = choice(video_list)
    author = await adapter.get_by_id(User, rand.author_id, session=session)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    like_objs = await adapter.get_by_values(
        Like,
        {"user_id": user.id, "video_id": rand.id},
        session=session,
    )
    like_obj = like_objs[0] if like_objs else None

    liked = like_obj.like is True if like_obj else False
    disliked = like_obj.like is False if like_obj else False

    response = VideoResponse.model_validate(rand, from_attributes=True)
    response.serv_url = f"{settings.backend_url}/stream-video/{rand.id}"
    response.author_name = author.name
    response.author_username = author.username
    response.is_liked_by_user = liked
    response.is_disliked_by_user = disliked

    return response
