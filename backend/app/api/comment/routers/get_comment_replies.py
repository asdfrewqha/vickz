from typing import Annotated, List, Optional
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


@router.get("/get-comment-replies/{comment_id}", response_model=List[Optional[CommentResponse]])
async def get_comment_replies(
    comment_id: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    comment = await adapter.get_by_id(Comment, comment_id, session=session)
    if not comment:
        raise HTTPException(404, "Comment not found")

    replies = await adapter.get_comment_replies(comment_id, session=session)
    if not replies:
        return []

    reply_ids = [r.id for r in replies]

    user_likes = {}
    if user:
        for uid in reply_ids:
            like = await adapter.get_by_values(
                CommentLike,
                and_conditions={"user_id": user.id},
                or_conditions={"comment_id": uid},
                mode="mixed",
                session=session,
            )
            if like:
                user_likes[like[0].comment_id] = like[0].like

    response = []
    for reply in replies:
        reply = CommentResponse.model_validate(reply, from_attributes=True)
        reply.is_liked_by_user = user_likes.get(reply.id) is True
        reply.is_disliked_by_user = user_likes.get(reply.id) is False
        response.append(reply)
    return response
