from typing import Annotated
from uuid import UUID

from app.api.comment.schemas import CommentCreate, CommentCreateResponse
from app.database.adapter import adapter
from app.database.models import Comment, User, Video
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/add-comment/{video_id}", response_model=CommentCreateResponse, status_code=201)
async def add_comment(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    content: CommentCreate,
    video_id: UUID,
    parent_id: UUID | None = None,
):
    if len(content.content) < 2:
        raise HTTPException(400, "Too short")
    video = await adapter.get_by_id(Video, video_id, session=session)
    if not video:
        raise HTTPException(404, "Video not found")
    if parent_id:
        parent_comment = await adapter.get_by_id(Comment, parent_id, session=session)
        if parent_comment:
            parent_username = parent_comment.user_username
            await adapter.update_by_id(
                Comment,
                parent_id,
                {"replies_count": parent_comment.replies_count + 1},
                session=session,
            )
    else:
        parent_username = None
    new_comment = {
        "user_id": user.id,
        "user_name": user.name,
        "user_username": user.username,
        "video_id": video_id,
        "parent_id": parent_id,
        "parent_username": parent_username,
        "content": content.content,
    }
    await adapter.update_by_id(Video, video_id, {"comments": video.comments + 1}, session=session)
    new_comm = await adapter.insert(Comment, new_comment, session=session)
    return CommentCreateResponse(id=new_comm.id)
