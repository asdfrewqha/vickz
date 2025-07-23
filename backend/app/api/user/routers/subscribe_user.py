from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.checks import check_user_token
from app.dependencies.responses import emptyresponse, okresponse
from app.database.adapter import adapter
from app.database.models import Subscription, User
from app.database.session import get_async_session


router = APIRouter()


@router.post("/subscribe/{uuid}")
async def subscribe(
    user: Annotated[User, Depends(check_user_token)],
    uuid: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    user_db = await adapter.get_by_id(User, uuid, session=session)
    if not user_db:
        raise HTTPException(404, "User not found")
    if user_db.id == user.id:
        raise HTTPException(403, "You can't subscribe to yourself")
    ex_subscription = await adapter.get_by_values(
        Subscription,
        {
            "subscriber_id": user.id,
            "subscribed_to_id": uuid,
        },
    )
    if ex_subscription:
        ex_subscription = ex_subscription[0]
        await adapter.delete(Subscription, ex_subscription.id, session=session)
        await adapter.update_by_id(
            User,
            uuid,
            {"followers_count": max(user_db.followers_count - 1, 0)},
            session=session,

        )
        await adapter.update_by_id(
            User,
            user.id,
            {"subscriptions_count": max(user.subscriptions_count - 1, 0)},
            session=session,
        )
        return emptyresponse()
    await adapter.insert(
        Subscription,
        {
            "subscriber_id": user.id,
            "subscribed_to_id": uuid,
        },
        session=session,
    )
    await adapter.update_by_id(User, uuid, {"followers_count": user_db.followers_count + 1}, session=session)
    await adapter.update_by_id(User, user.id, {"subscriptions_count": user.subscriptions_count + 1}, session=session)
    return okresponse("Subscribed successfully")
