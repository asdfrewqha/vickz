from uuid import UUID
from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, View
from app.database.session import get_async_session


router = APIRouter()


@router.get("/get-views", response_model=List[UUID])
async def get_views(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    views = await adapter.get_by_value(View, "user_id", user.id, session=session)
    views = [str(x.video_id) for x in views]
    return views
