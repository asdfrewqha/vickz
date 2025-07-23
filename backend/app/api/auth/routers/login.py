from typing import Annotated
import re

from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import UserLogin
from app.database.adapter import adapter
from app.database.models import User
from app.api.auth.utils import verify_password
from app.utils.token_manager import TokenManager
from app.database.session import get_async_session


router = APIRouter()


def is_valid_email(value: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, value))


def is_valid_username(value: str) -> bool:
    pattern = r"^[a-zA-Z0-9_]{3,}$"
    return bool(re.match(pattern, value))


@router.post("/login", status_code=status.HTTP_200_OK)
async def token(
    user: UserLogin,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    if is_valid_email(user.identifier):
        bd_user = await adapter.get_by_value(User, "email", user.identifier, session=session)
    elif is_valid_username(user.identifier):
        bd_user = await adapter.get_by_value(User, "username", f"@{user.identifier}", session=session)
    else:
        raise HTTPException(400, "Invalid identifier")

    if not bd_user:
        raise HTTPException(404, "User not found")

    bd_user = bd_user[0]

    if not verify_password(user.password, bd_user.hashed_password):
        raise HTTPException(403, "Forbidden")

    response = JSONResponse({"message": "success", "status": "success"})
    response.set_cookie("access_token", TokenManager.create_token({"sub": str(bd_user.id)}))
    response.set_cookie("refresh_token", TokenManager.create_token({"sub": str(bd_user.id)}, False))

    return response
