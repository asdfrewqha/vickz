from typing import Annotated, List
from uuid import UUID

from app.database.adapter import adapter
from app.database.models import User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/get-videos-by-user-id/{uuid}", response_model=List[UUID])
async def get_videos_by_user_id(
    uuid: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    videos = await adapter.get_by_value(Video, "author_id", uuid, session=session)
    if not videos:
        raise HTTPException(404, "Videos not found")
    return [str(video.id) for video in videos]
