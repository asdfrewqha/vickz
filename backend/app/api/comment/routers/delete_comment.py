from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.checks import check_user_token
from app.dependencies.responses import emptyresponse
from app.database.adapter import adapter
from app.database.models import User, Comment, Video
from app.database.session import get_async_session


router = APIRouter()


@router.delete("/delete-comment/{comment_id}", status_code=204)
async def delete_comment(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    comment_id: UUID
):
    comment = await adapter.get_by_id(Comment, comment_id, session=session)
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(403, "Forbidden")
    video = await adapter.get_by_id(Video, comment.video_id, session=session)
    if not video:
        raise HTTPException(404, "Video not found")
    await adapter.delete(Comment, comment_id, session=session)
    await adapter.update_by_id(Video, comment.video_id, {"comments": max(video.comments - 1, 0)}, session=session)
    return emptyresponse()
