from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import Video, User


router = APIRouter()


@router.get("/get-videos-by-user-id/{uuid}", response_model=List[UUID])
async def get_videos_by_user_id(uuid: UUID, user: Annotated[User, Depends(check_user_token)]):
    videos = await adapter.get_by_value(Video, "author_id", uuid)
    if not videos:
        raise HTTPException(404, "Videos not found")
    return [str(video.id) for video in videos]
