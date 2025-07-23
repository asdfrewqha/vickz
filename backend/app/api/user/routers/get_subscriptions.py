from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, Subscription
from app.database.session import get_async_session


router = APIRouter()


@router.get("/get-subscriptions", response_model=List[UUID])
async def get_subscriptions(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    subscribes = await adapter.get_by_value(Subscription, "subscriber_id", user.id, session=session)
    list_subscribes = []
    for sub in subscribes:
        list_subscribes.append(str(sub.subscribed_to_id))
    return list_subscribes
