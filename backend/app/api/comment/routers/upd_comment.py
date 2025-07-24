from typing import Annotated
from uuid import UUID

from app.api.comment.schemas import CommentCreate
from app.database.adapter import adapter
from app.database.models import Comment, User
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from app.dependencies.responses import okresponse
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.put("/edit-comment/{comment_id}")
async def edit_comment(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    comment_id: UUID,
    content: CommentCreate,
):
    if len(content.content) < 2:
        raise HTTPException(400, "Too short")
    comment = await adapter.get_by_id(Comment, comment_id, session=session)
    if not comment:
        raise HTTPException(404, "Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(403, "Forbidden")
    await adapter.update_by_id(Comment, comment_id, {"content": content.content}, session=session)
    return okresponse()
