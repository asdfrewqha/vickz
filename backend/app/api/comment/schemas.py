from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CommentCreate(BaseModel):
    content: str


class CommentCreateResponse(BaseModel):
    id: UUID


class CommentResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    user_username: str
    parent_id: Optional[UUID] = None
    parent_username: Optional[str] = None
    content: str
    likes: int
    dislikes: int
    replies_count: int
    is_liked_by_user: Optional[bool] = False
    is_disliked_by_user: Optional[bool] = False
