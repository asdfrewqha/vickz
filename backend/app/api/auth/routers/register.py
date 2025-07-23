from typing import Annotated
import secrets
import string

from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.tasks import send_confirmation_email
from app.dependencies.responses import okresponse, badresponse
from app.api.auth.schemas import UserCreate
from app.database.adapter import adapter
from app.database.models import User
from app.database.session import get_async_session
from app.utils.redis_adapter import redis_adapter
from app.core.logging import get_logger

logger = get_logger()

router = APIRouter()


def generate_secure_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


@router.post("/register", status_code=status.HTTP_200_OK)
async def register(
    user: UserCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    email_check = await adapter.get_by_value(User, "email", user.email, session=session)
    if email_check:
        raise HTTPException(409, "Email already exists")

    username_check = await adapter.get_by_value(User, "username", user.username, session=session)
    if username_check:
        raise HTTPException(409, "Username already exists")

    random_code = generate_secure_code()
    await redis_adapter.set(f"email_verification_code:{user.email}", random_code, expire=600)
    response = send_confirmation_email.delay(user.email, random_code)
    if response:
        return okresponse("Code sent succesfully", 200)
    return badresponse("Error with mail server", 500)
