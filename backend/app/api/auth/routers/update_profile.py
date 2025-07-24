from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import UpdateProfile
from app.dependencies.responses import okresponse
from app.dependencies.checks import check_user_token
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session

router = APIRouter()


@router.put("/update-profile")
async def upd_profile(
    user: Annotated[User, Depends(check_user_token)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    update: UpdateProfile,
):
    updated_data = {}
    uid = user.id

    if update.name:
        updated_data["name"] = update.name

    if update.username:
        update.username = f"@{update.username}"
        existing_username = await adapter.get_by_value(User, "username", update.username, session=session)
        if not existing_username:
            updated_data["username"] = update.username
        else:
            raise HTTPException(409, "Username already taken")

    if update.description:
        updated_data["description"] = update.description

    if not updated_data:
        raise HTTPException("No fields provided")

    await adapter.update_by_id(User, uid, updated_data, session=session)
    return okresponse(message="Profile updated successfully")
