from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.responses import okresponse
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import Comment, CommentLike, User
from app.database.session import get_async_session

router = APIRouter()


@router.post("/like-comment/{comment_id}")
async def like_comment(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    comment_id: UUID,
    like: bool = True,
):
    comment = await adapter.get_by_id(Comment, comment_id, session=session)
    if not comment:
        raise HTTPException(404, "Video not found")
    existing_like = await adapter.get_by_values(
        CommentLike,
        {"user_id": user.id, "comment_id": comment_id},
        session=session,
    )
    if existing_like:
        prev_like = existing_like[0]
        await adapter.delete(CommentLike, prev_like.id, session=session)

        if prev_like.like:
            comment.likes = max(comment.likes - 1, 0)
        else:
            comment.dislikes = max(comment.dislikes - 1, 0)

        if prev_like.like == like:
            await adapter.update_by_id(
                Comment,
                comment_id,
                {"likes": comment.likes, "dislikes": comment.dislikes},
                session=session
            )
            return okresponse(message=f"{'liked' if like else 'disliked'}")

    await adapter.insert(CommentLike, {"user_id": user.id, "comment_id": comment_id, "like": like}, session=session)

    if like:
        comment.likes += 1
    else:
        comment.dislikes += 1

    await adapter.update_by_id(
        Comment,
        comment_id,
        {"likes": comment.likes, "dislikes": comment.dislikes},
        session=session
    )

    return okresponse(message=f"{'liked' if like else 'disliked'}")
