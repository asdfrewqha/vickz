from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.comment.schemas import CommentResponse
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, Comment, CommentLike, Video
from app.database.session import get_async_session


router = APIRouter()


@router.get("/get-comments/{video_id}", response_model=List[Optional[CommentResponse]])
async def get_comments(
    video_id: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    video = await adapter.get_by_id(Video, video_id, session=session)
    if not video:
        raise HTTPException(404, "Video not found")
    root_comments = await adapter.get_by_values(Comment, {"video_id": video_id, "parent_id": None}, session=session)
    if not root_comments:
        return []
    comment_ids = [c.id for c in root_comments]
    user_likes = {}
    if user:
        for uid in comment_ids:
            like = await adapter.get_by_values(
                CommentLike,
                and_conditions={"user_id": user.id},
                or_conditions={"comment_id": uid},
                mode="mixed",
                session=session
            )
            if like:
                user_likes[like[0].comment_id] = like[0].like
    result = []
    for c in root_comments:
        liked = user_likes.get(c.id) is True
        disliked = user_likes.get(c.id) is False
        comment = CommentResponse.model_validate(c, from_attributes=True)
        comment.is_liked_by_user = liked
        comment.is_disliked_by_user = disliked
        result.append(comment)
    return result
