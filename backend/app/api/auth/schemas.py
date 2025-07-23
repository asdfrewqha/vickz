from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    password: str
    description: Optional[str] = ""


class UserRegResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    username: str
    description: Optional[str] = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserLogin(BaseModel):
    identifier: str
    password: str
