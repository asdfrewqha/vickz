from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException


from app.api.video.schemas import UpdateVideoContent
from app.dependencies.checks import check_user_token
from app.dependencies.responses import okresponse
from app.database.adapter import adapter
from app.database.models import User, Video


router = APIRouter()


@router.put("/update-video/{uuid}")
async def update_video(
    user: Annotated[User, Depends(check_user_token)],
    uuid: UUID,
    content: UpdateVideoContent,
):
    if not user:
        raise HTTPException(401, "Unauthorized")
    video = await adapter.get_by_id(Video, uuid)
    if not video:
        raise HTTPException(404, "Video not found")
    if video.author_id != user.id:
        raise HTTPException(403, "Forbidden")
    video_dict = UpdateVideoContent.model_dump(content)
    await adapter.update_by_id(Video, uuid, video_dict)
    return okresponse()
