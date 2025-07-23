from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.user.schemas import UserResponse
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, Subscription
from app.database.session import get_async_session


router = APIRouter()


@router.get("/get-user/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)]
):
    if not username.startswith("@"):
        username = f"@{username}"
    user_bd = await adapter.get_by_value(User, "username", username, session=session)
    if not user_bd:
        raise HTTPException("User not found", 404)
    user_bd = user_bd[0]
    response = UserResponse.model_validate(user_bd, from_attributes=True)
    sub = await adapter.get_by_values(Subscription, {"subscriber_id": user.id, "subscribed_to_id": user_bd.id}, session=session)
    if sub:
        response.is_subscribed = True
    return response
