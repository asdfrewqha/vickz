from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict


class VideoCreateResponse(BaseModel):
    url: str
    uuid: UUID


class VideoResponse(BaseModel):
    id: UUID
    url: str
    serv_url: Optional[str] = None
    author_id: UUID
    author_name: Optional[str] = None
    author_username: Optional[str] = None
    is_liked_by_user: Optional[bool] = False
    is_disliked_by_user: Optional[bool] = False
    views: int = 0
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    description: str = ""
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UpdateVideoContent(BaseModel):
    description: str
