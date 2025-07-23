from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from app.core.settings import settings


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    name: str
    avatar_url: str = settings.default_avatar_url
    description: str = ""
    followers_count: int = 0
    subscriptions_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserResponse(BaseModel):
    id: UUID
    username: str
    name: str
    avatar_url: str = settings.default_avatar_url
    followers_count: int = 0
    subscriptions_count: int = 0
    is_subscribed: bool = False
    description: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)
