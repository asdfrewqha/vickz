from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.comment.schemas import CommentResponse
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, Comment, CommentLike
from app.database.session import get_async_session

router = APIRouter()


@router.get("/get-comment/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    comment = await adapter.get_by_id(Comment, comment_id, session=session)
    if not comment:
        raise HTTPException(404, "Comment not found")
    liked = False
    disliked = False
    ex_like = await adapter.get_by_value(CommentLike, "user_id", user.id, session=session)
    if ex_like:
        liked = True if ex_like[0].like is True else False
        disliked = True if ex_like[0].like is False else False
    response = CommentResponse.model_validate(comment, from_attributes=True)
    response.is_disliked_by_user = liked
    response.is_disliked_by_user = disliked
    return response
