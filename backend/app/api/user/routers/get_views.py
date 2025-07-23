from uuid import UUID
from typing import Annotated, List

from fastapi import APIRouter, Depends

from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User, View


router = APIRouter()


@router.get("/get-views", response_model=List[UUID])
async def get_views(user: Annotated[User, Depends(check_user_token)]):
    views = await adapter.get_by_value(View, "user_id", user.id)
    views = [str(x.video_id) for x in views]
    return views
