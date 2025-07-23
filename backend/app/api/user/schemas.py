from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


class UserProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    name: str
    description: str = ""
    followers_count: int = 0
    subscriptions_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)
