from typing import Annotated, Dict, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.user.schemas import UserResponse
from app.utils.cookies import get_tokens_cookies
from app.utils.token_manager import TokenManager
from app.database.adapter import adapter
from app.database.models import User, Subscription
from app.database.session import get_async_session


router = APIRouter()


@router.get("/get-user/{id}", response_model=UserResponse)
async def get_user(
    id: UUID,
    tokens: Annotated[Dict[Literal["access", "refresh"], str], Depends(get_tokens_cookies)],
    session: Annotated[AsyncSession, Depends(get_async_session)]
):
    user_bd = await adapter.get_by_id(User, id, session=session)
    if not user_bd:
        raise HTTPException("User not found", 404)
    response = UserResponse.model_validate(user_bd, from_attributes=True)
    token_data = TokenManager.decode_token(tokens["access"])
    if token_data:
        if token_data.get("sub"):
            user = await adapter.get_by_id(User, token_data.get("sub"), session=session)
            if user:
                sub = await adapter.get_by_values(Subscription, {"subscriber_id": user.id, "subscribed_to_id": user_bd.id}, session=session)
                if sub:
                    response.is_subscribed = True
    return response
