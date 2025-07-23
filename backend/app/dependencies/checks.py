from typing import Annotated, Dict, Literal
from uuid import UUID

from app.utils.token_manager import TokenManager
from app.utils.cookies import get_tokens_cookies
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException
from app.core.logging import get_logger

logger = get_logger()


async def check_user_token(
    tokens: Annotated[Dict[Literal["access", "refresh"], str], Depends(get_tokens_cookies)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    data = TokenManager.decode_token(tokens["access"])
    user = await adapter.get_by_id(User, UUID(data["sub"]), session=session)
    if user:
        return user

    logger.error("No user for this token")
    raise HTTPException(401, "No user for this token")


async def check_refresh(
    tokens: Annotated[Dict[Literal["access", "refresh"], str], Depends(get_tokens_cookies)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    data = TokenManager.decode_token(tokens["refresh"], access=False)
    user = await adapter.get_by_id(User, UUID(data["sub"]), session=session)
    if user:
        return user

    logger.error("No user for this token")
    raise HTTPException(404, "No user for this token")
