from typing import Annotated

from fastapi import APIRouter, Response, status, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import UserCreate, UserRegResponse
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session
from app.utils.redis_adapter import redis_adapter
from app.api.auth.utils import get_password_hash
from app.utils.token_manager import TokenManager

router = APIRouter()


@router.post("/register-confirm/{code}", response_model=UserRegResponse, status_code=status.HTTP_201_CREATED)
async def confirm_registration(
    response: Response,
    user: UserCreate,
    code: str,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    code_verify = await redis_adapter.get(f"email_verification_code:{user.email}")
    if not code_verify or code != code_verify:
        raise HTTPException(401, "Invalid code")

    new_user = {
        "email": user.email,
        "name": user.name,
        "username": f"@{user.username}",
        "hashed_password": get_password_hash(user.password),
        "description": user.description,
    }

    new_user_db = await adapter.insert(User, new_user, session=session)

    response.set_cookie("access_token", TokenManager.create_token({"sub": str(new_user_db.id)}))
    response.set_cookie("refresh_token", TokenManager.create_token({"sub": str(new_user_db.id)}, False))

    return UserRegResponse.model_validate(new_user_db, from_attributes=True)
