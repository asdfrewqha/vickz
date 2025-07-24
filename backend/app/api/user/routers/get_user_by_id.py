from typing import Annotated
from uuid import UUID

from app.api.user.schemas import UserResponse
from app.database.adapter import adapter
from app.database.models import Subscription, User
from app.database.session import get_async_session
from app.dependencies.checks import check_user_token
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/get-user/{id}", response_model=UserResponse)
async def get_user(
    id: UUID,
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    user_bd = await adapter.get_by_id(User, id, session=session)
    if not user_bd:
        raise HTTPException(404, "User not found")
    response = UserResponse.model_validate(user_bd, from_attributes=True)
    sub = await adapter.get_by_values(
        Subscription, {"subscriber_id": user.id, "subscribed_to_id": user_bd.id}, session=session
    )
    if sub:
        response.is_subscribed = True
    return response
