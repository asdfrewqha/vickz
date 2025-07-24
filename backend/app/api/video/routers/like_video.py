from typing import Annotated
from uuid import UUID

from app.database.adapter import adapter
from app.database.models import Like, User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from app.dependencies.responses import okresponse
from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/like-video")
async def like_video(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    like: bool = Query(True),
):
    video = await adapter.get_by_id(Video, uuid, session=session)
    if not video:
        raise HTTPException(404, "Video not found")

    existing_like = await adapter.get_by_values(
        Like, {"user_id": user.id, "video_id": uuid}, session=session
    )

    if existing_like:
        prev_like = existing_like[0]
        await adapter.delete(Like, prev_like.id, session=session)

        if prev_like.like:
            video.likes = max(video.likes - 1, 0)
        else:
            video.dislikes = max(video.dislikes - 1, 0)

        if prev_like.like == like:
            await adapter.update_by_id(
                Video, uuid, {"likes": video.likes, "dislikes": video.dislikes}, session=session
            )
            return okresponse(message=f"{'liked' if like else 'disliked'}")

    await adapter.insert(
        Like, {"user_id": user.id, "video_id": uuid, "like": like}, session=session
    )

    if like:
        video.likes += 1
    else:
        video.dislikes += 1

    await adapter.update_by_id(
        Video, uuid, {"likes": video.likes, "dislikes": video.dislikes}, session=session
    )

    return okresponse(message=f"{'liked' if like else 'disliked'}")
